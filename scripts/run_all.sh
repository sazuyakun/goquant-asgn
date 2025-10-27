# zsh
SESSION="goquant"

# Kill existing session (optional)
tmux has-session -t $SESSION 2>/dev/null
if [ $? == 0 ]; then
    echo "Killing existing tmux session: $SESSION"
    tmux kill-session -t $SESSION
fi

echo "Starting new tmux session: $SESSION"
tmux new-session -d -s $SESSION

# Window 1: Docker Compose
tmux rename-window -t $SESSION:0 'docker'
tmux send-keys -t $SESSION:0 'docker-compose up' C-m

# Window 2: Consumers
tmux new-window -t $SESSION:1 -n 'consumers'
tmux send-keys -t $SESSION:1 'poetry run python src/goquant/main.py consumer logger' C-m
tmux split-window -v -t $SESSION:1
tmux send-keys -t $SESSION:1.1 'poetry run python src/goquant/main.py consumer signal' C-m
tmux split-window -v -t $SESSION:1
tmux send-keys -t $SESSION:1.2 'poetry run python src/goquant/main.py consumer aggregator' C-m
tmux split-window -v -t $SESSION:1
tmux send-keys -t $SESSION:1.3 'poetry run python src/goquant/main.py consumer sentiment' C-m

# Window 3: Producers
tmux new-window -t $SESSION:2 -n 'producers'
tmux send-keys -t $SESSION:2 'poetry run python src/goquant/main.py producer market' C-m
tmux split-window -v -t $SESSION:2
tmux send-keys -t $SESSION:2.1 'poetry run python src/goquant/main.py producer news' C-m
tmux split-window -v -t $SESSION:2
tmux send-keys -t $SESSION:2.2 'poetry run python src/goquant/main.py producer reddit' C-m

# Layouts
tmux select-layout -t $SESSION:1 tiled
tmux select-layout -t $SESSION:2 tiled

# Attach
tmux attach -t $SESSION
