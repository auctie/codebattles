const roomId = window.location.pathname.split('/').pop();

const myEditor = document.getElementById('myEditor');
const opponentEditor = document.getElementById('opponentEditor');
const roomStatusSpan = document.getElementById('roomStatus');
const runBtn = document.getElementById('runBtn');
const stdoutArea = document.getElementById('stdoutArea');
const answerField = document.getElementById('answerField');
const submitAnswerBtn = document.getElementById('submitAnswerBtn');
const answerFeedback = document.getElementById('answerFeedback');
const problemContent = document.getElementById('problemContent')

const ws = new WebSocket(`ws://${window.location.host}/ws/${roomId}`);

ws.onopen = () => {
    roomStatusSpan.innerText = '~ Waiting for opponent';
    roomStatusSpan.className = 'room-status waiting';
};

ws.onmessage = (event) => {
    let msg;
    try {
        msg = JSON.parse(event.data);
    } catch {
        console.warn('Invalid JSON:', event.data);
        return;
    }

    switch (msg.type) {
        case 'update_code':
            opponentEditor.value = msg.content;
            break;
        case 'opponent_joined':
            roomStatusSpan.innerText = '~ Both players joined';
            roomStatusSpan.className = 'room-status connected';
            problemText.innerText = msg.content[1];
            break;
        case 'opponent_left':
            roomStatusSpan.innerText = '~ Opponent disconnected.';
            roomStatusSpan.className = 'room-status error';
            myEditor.disabled = true;
            break;
        case 'error':
            roomStatusSpan.innerText = `${msg.message}`;
            roomStatusSpan.className = 'room-status error';
            if (msg.message.includes('full')) myEditor.disabled = true;
            break;
        default:
            console.log('Unknown type:', msg.type);
    }
};

ws.onclose = (event) => {
    if (event.code === 1008) {
        roomStatusSpan.innerText = `Room full: ${event.reason || 'only 2 players'}`;
    } else {
        roomStatusSpan.innerText = 'Refresh to try again.';
    }
    roomStatusSpan.className = 'room-status error';
    myEditor.disabled = true;
    opponentEditor.disabled = true;
};

myEditor.addEventListener('input', () => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'update_code',
            content: myEditor.value
        }));
    }
});

runBtn.addEventListener('click', async () => {
    const code = myEditor.value;
    stdoutArea.innerText = "Running code...";

    try {
        const response = await fetch('/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: code })
        });
        const data = await response.json();
        stdoutArea.innerText = data.output || "No output.";
    } catch (err) {
        stdoutArea.innerText = `Error: ${err.message}`;
    }
});

submitAnswerBtn.addEventListener('click', () => {
    const answer = answerField.value.trim();
    if (!answer) {
        answerFeedback.innerText = 'Provide an answer.';
        answerFeedback.className = 'answer-feedback incorrect';
        return;
    }

    if (answer === '42') {
        answerFeedback.innerText = 'Correct! Well done.';
        answerFeedback.className = 'answer-feedback correct';
    } else {
        answerFeedback.innerText = 'Incorrect.';
        answerFeedback.className = 'answer-feedback incorrect';
    }
});

setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
    }
}, 30000);

const savedName = sessionStorage.getItem('playerName');
if (savedName) {
    const nameElement = document.getElementById('name');
    if (nameElement) nameElement.innerText = `${savedName}`;
} else {
    fetch('/api/user-data')
        .then(response => response.json())
        .then(data => {
            const playerName = data['name'];
            sessionStorage.setItem('playerName', playerName);
            document.getElementById('name').innerText = `${playerName}`;
        })
        .catch(err => console.error('Failed to load nickname:', err));
}