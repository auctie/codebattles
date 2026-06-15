document.getElementById('joinBtn').addEventListener('click', () => {
    let room = document.getElementById('roomName').value.trim();
    if (!room) room = 'default_room';
    window.location.href = `/battle/${encodeURIComponent(room)}`;
});

document.getElementById('roomName').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        document.getElementById('joinBtn').click();
    }
});

let playerName = sessionStorage.getItem('playerName');
let playerId = sessionStorage.getItem('playerId');
if (!playerId) {
    playerId = crypto.randomUUID();
    sessionStorage.setItem('playerId', playerId);
}

function startWebSocket(name, id) {
    const ws = new WebSocket(`/ws/lobby?name=${encodeURIComponent(name)}&id=${encodeURIComponent(id)}`);
    ws.onopen = () => console.log(`${id} connected to lobby`);
    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        switch (msg.type) {
            case 'online_list':
                updatePlayerList(msg.players);
                break;
            case 'player_joined':
                addPlayer(msg.player);
                break;
            case 'player_left':
                removePlayer(msg.player.id);
                break;
            default:
                console.warn('Unknown message type:', msg.type);
        }
    };
    window.lobbyWs = ws;
}

if (!playerName) {
    fetch('/api/user-name')
        .then(response => response.json())
        .then(data => {
            playerName = data.name;
            sessionStorage.setItem('playerName', playerName);
            document.getElementById('name').innerText = playerName;
            startWebSocket(playerName, playerId);
        })
        .catch(err => {
            console.error('Failed to load nickname:', err);
            playerName = 'Anonymous';
            document.getElementById('name').innerText = playerName;
            startWebSocket(playerName, playerId);
        });
} else {
    document.getElementById('name').innerText = playerName;
    startWebSocket(playerName, playerId);
}

function updatePlayerList(players) {
    const pl = document.getElementById('playerList');
    pl.innerHTML = '';
    players.forEach(player => {
        addPlayer(player);
    });
}

function addPlayer(player) {
    const pl = document.getElementById('playerList');
    const li = document.createElement('li');
    li.id = `player-${player.id}`;
    li.innerText = player.name;
    const inviteBtn = document.createElement('button');
    inviteBtn.innerText = 'Invite';
    inviteBtn.onclick = () => invitePlayer(player.id, player.name);
    li.appendChild(inviteBtn);
    pl.appendChild(li);
}

function removePlayer(playerId) {
    const el = document.getElementById(`player-${playerId}`);
    if (el) el.remove();
}

document.getElementById('showPlayersBtn').addEventListener('click', () => {
    const container = document.getElementById('playerListContainer');
    container.style.display = container.style.display === 'none' ? 'block' : 'none';
});

function invitePlayer(targetId, targetName) {
    console.log(`Inviting ${targetName} (${targetId})`);
    // Later: send a message via WebSocket
    // ws.send(JSON.stringify({ type: 'invite', to: targetId }));
}