autoload -Uz compinit && compinit
autoload -Uz vcs_info
setopt PROMPT_SUBST
zstyle ':vcs_info:git:*' formats '%F{green}%b%f '
precmd() { vcs_info }
PROMPT='%F{yellow}[dc]%f ${vcs_info_msg_0_}%F{blue}%~%f $ '

[ -f /usr/share/doc/fzf/examples/key-bindings.zsh ] && source /usr/share/doc/fzf/examples/key-bindings.zsh

bindkey -v
export EDITOR=vim
