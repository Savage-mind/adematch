document.addEventListener('DOMContentLoaded', function() {
    const eventContainer = document.getElementById('event');
    const likeBtn = document.getElementById('like-btn');    const dislikeBtn = document.getElementById('dislike-btn');
  

    function loadNextEvent() {
        fetch('/api/events/next')
            .then(response => response.json())
            .then(data => {
                if (data.event) {
                    const event = data.event;
                    eventContainer.innerHTML = `
                        <h2>${event.name}</h2>
                        <p>Date: ${event.date}</p>
                        <p>Venue: ${event.venue}</p>
                        <p>Artists: ${event.artists.join(', ')}</p>
                    `;
                } else {
                    eventContainer.innerHTML = '<p>No more events. Check your matches!</p>';
                    likeBtn.style.display = 'none';
                    dislikeBtn.style.display = 'none';
                }
            });
    }

    likeBtn.addEventListener('click', function() {
        fetch('/api/events/like', {method: 'POST'})
            .then(() => loadNextEvent());
    });

    dislikeBtn.addEventListener('click', function() {
        fetch('/api/events/dislike', {method: 'POST'})
            .then(() => loadNextEvent());
    });

    loadNextEvent();
});
