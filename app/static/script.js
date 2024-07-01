document.addEventListener("DOMContentLoaded", function() {
    function fetchWidget(widgetId) {
        fetch(`/widget/${widgetId}`)
            .then(response => response.json())
            .then(data => {
                const widgetDiv = document.getElementById(`widget-${widgetId}`);
                const contentDiv = widgetDiv.querySelector('.widget-content');
                contentDiv.innerHTML = data.content;
            })
            .catch(error => console.error(`Error fetching widget ${widgetId}:`, error));
    }

    // Fetch widgets every 30 seconds
    function refreshWidgets() {
        const widgetDivs = document.querySelectorAll('.widget');
        widgetDivs.forEach(div => {
            const widgetId = div.id.split('-')[1];
            fetchWidget(widgetId);
        });
    }

    setInterval(refreshWidgets, 30000);
    refreshWidgets(); // Initial fetch
});
