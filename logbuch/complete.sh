# logbuch completion                             -*- shell-script -*-
# shellcheck shell=bash

# for _apt_get
source /usr/share/bash-completion/completions/apt-get

_logbuch_completion() {
    local cur prev words cword
    _init_completion || return
    [ -z "${DEBUG-}" ] || echo -e "\n_logbuch_completion before: cur '$cur' prev '$prev' words(${#words[@]}): '${words[0]}' '${words[1]}' '${words[2]}' cword '$cword' COMP_WORDS: '${COMP_WORDS[*]}' COMP_CWORD: '$COMP_CWORD' COMP_LINE: '$COMP_LINE' COMP_POINT: '$COMP_POINT'"

    word_length="${#words[@]}"  # save the size before, as it changes in the loop
    for ((i=word_length-1; i>=1; i--)); do # shift all arguments on to the right, starting right to not overwrite the own values
        words[i+1]="${words[$i]}"
    done

    case "${words[0]}" in
        # all apt-get commands from https://hg.intevation.de/adminton/file/tip/logbuch-tools/logbuch-installer
        apt-install)
            words[1]='install'
            ;;
        apt-remove)
            words[1]='remove'
            ;;
        apt-autoremove)
            words[1]='autoremove'
            ;;
        apt-build-dep)
            words[1]='build-dep'
            ;;
        apt-upgrade)
            words[1]='upgrade'
            ;;
        apt-dist-upgrade)
            words[1]='dist-upgrade'
            ;;
        *)
            # not supported
            return
            ;;
    esac
    words[0]='apt-get'
    # Set the new words
    COMP_WORDS=("${words[@]}")  # parentheses are important to keep the last element with an empty string
    # set the word to complete to one after ('apt-get install' is one word and 4 characters longer than 'apt-install')
    ((COMP_CWORD+=1))
    ((COMP_POINT+=4))
    COMP_LINE="${words[*]}"

    # Delegate to the main _apt completion function
    _apt_get
}

complete -F _logbuch_completion apt-install
complete -F _logbuch_completion apt-remove
complete -F _logbuch_completion apt-autoremove
complete -F _logbuch_completion apt-build-dep
complete -F _logbuch_completion apt-upgrade
complete -F _logbuch_completion apt-dist-upgrade
