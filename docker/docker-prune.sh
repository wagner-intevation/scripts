#!/bin/bash
LC_ALL=C

# Initialize filter string
FILTERS="--filter \"until=$((30*24))h\""

# Check if config file is provided as first parameter
if [ -n "$1" ] && [ -f "$1" ]; then
  # Source the configuration file
  source "$1"

  # Add label filters if variables are set
  if [ -n "$PRUNE_EXCEPTION_IMAGE" ]; then
    FILTERS="$FILTERS --filter \"label!=com.docker.compose.image=$PRUNE_EXCEPTION_IMAGE\""
  fi

  if [ -n "$PRUNE_EXCEPTION_PROJECT_WORKING_DIR" ]; then
    FILTERS="$FILTERS --filter \"label!=com.docker.compose.project.working_dir=$PRUNE_EXCEPTION_PROJECT_WORKING_DIR\""
  fi

  if [ -n "$PRUNE_EXCEPTION_PROJECT" ]; then
    FILTERS="$FILTERS --filter \"label!=com.docker.compose.project=$PRUNE_EXCEPTION_PROJECT\""
  fi

  if [ -n "$PRUNE_EXCEPTION_MAINTAINER" ]; then
    FILTERS="$FILTERS --filter \"label!=maintainer=$PRUNE_EXCEPTION_MAINTAINER\""
  fi
fi

# Execute docker commands with filters
{
  echo "Running docker system prune -af $FILTERS:"
  eval "docker system prune -af $FILTERS"
  echo "Running docker image prune -f --filter \"until=$((7*24))h\""
  docker image prune -f --filter "until=$((7*24))h:"
} 2>&1 | tee >(systemd-cat -t docker-prune) | grep -Fxv 'Total reclaimed space: 0B'
