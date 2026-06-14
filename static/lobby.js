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