document.addEventListener("DOMContentLoaded", function() {
    var city = "{{ announcement.city }}";
    var region = "{{ announcement.region }}";

    var url = "https://nominatim.openstreetmap.org/search?city=" + city + "&state=" + region + "&format=json";

    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data && data[0]) {
                var lat = data[0].lat;
                var lon = data[0].lon;
                var map = L.map('map').setView([lat, lon], 13);

                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                }).addTo(map);

                L.marker([lat, lon]).addTo(map)
                    .bindPopup("{{ announcement.title }}")
                    .openPopup();
            }
        })
        .catch(error => {
            console.error("Помилка при отриманні координат:", error);
        });
});


// Ініціалізація карти (наприклад, Google Maps або Leaflet)
function initMap() {
    // Перевірка підтримки геолокації
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            var userLat = position.coords.latitude;
            var userLng = position.coords.longitude;

            // Ініціалізація карти
            var userLocation = {lat: userLat, lng: userLng};
            var map = new google.maps.Map(document.getElementById("map"), {
                center: userLocation,
                zoom: 12
            });

            // Додавання маркера для користувача
            var marker = new google.maps.Marker({
                position: userLocation,
                map: map,
                title: "Ваше місцезнаходження"
            });

            // Додавання фільтрації за координатами
            filterAnnouncements(userLat, userLng);
        });
    } else {
        alert("Ваш браузер не підтримує геолокацію.");
    }
}

// Функція для фільтрації оголошень за координатами
function filterAnnouncements(userLat, userLng) {
    // Отримання всіх оголошень
    const announcements = document.querySelectorAll('.announcement');

    announcements.forEach(announcement => {
        // Отримуємо координати оголошення
        const annLat = parseFloat(announcement.dataset.latitude);
        const annLng = parseFloat(announcement.dataset.longitude);

        // Обчислюємо відстань між користувачем та оголошенням
        const distance = calculateDistance(userLat, userLng, annLat, annLng);

        // Відображення оголошень на основі відстані (наприклад, до 10 км)
        if (distance <= 10) {
            announcement.style.display = 'block';  // Показуємо оголошення
        } else {
            announcement.style.display = 'none';   // Приховуємо оголошення
        }
    });
}

// Функція для обчислення відстані між двома точками
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Радіус Землі в км
    const dLat = toRadians(lat2 - lat1);
    const dLon = toRadians(lon2 - lon1);
    const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) *
        Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c; // Відстань в км
}

// Функція для конвертації градусів в радіани
function toRadians(degrees) {
    return degrees * (Math.PI / 180);
}

// Ініціалізуємо карту
window.onload = initMap;
document.addEventListener('DOMContentLoaded', function () {
    const locationInput = document.getElementById('location');
    const regionInput = document.getElementById('region');

    locationInput.addEventListener('input', function () {
        const query = locationInput.value;

        if (query.length >= 3) { // мінімум 3 символи для пошуку
            fetch(`https://api.geonames.org/searchJSON?q=${query}&maxRows=10&username=your_geonames_username`)
                .then(response => response.json())
                .then(data => {
                    const cities = data.geonames;
                    const suggestions = cities.map(city => ({
                        name: city.name,
                        region: city.adminName1
                    }));

                    showSuggestions(suggestions);
                })
                .catch(error => console.error('Error fetching city data:', error));
        }
    });

    function showSuggestions(suggestions) {
        const suggestionList = document.createElement('ul');
        suggestionList.classList.add('suggestions-list');

        suggestions.forEach(suggestion => {
            const listItem = document.createElement('li');
            listItem.textContent = `${suggestion.name}, ${suggestion.region}`;
            listItem.addEventListener('click', function () {
                locationInput.value = suggestion.name;
                regionInput.value = suggestion.region;
                clearSuggestions();
            });
            suggestionList.appendChild(listItem);
        });

        clearSuggestions();
        locationInput.parentElement.appendChild(suggestionList);
    }

    function clearSuggestions() {
        const existingSuggestions = document.querySelector('.suggestions-list');
        if (existingSuggestions) {
            existingSuggestions.remove();
        }
    }
});
document.addEventListener("DOMContentLoaded", function () {
    const profilePhoto = document.getElementById("profilePhoto");
    const dropdownMenu = document.getElementById("dropdownMenu");

    profilePhoto.addEventListener("click", function () {
        dropdownMenu.style.display = dropdownMenu.style.display === "block" ? "none" : "block";
    });

    document.addEventListener("click", function (event) {
        if (!profilePhoto.contains(event.target) && !dropdownMenu.contains(event.target)) {
            dropdownMenu.style.display = "none";
        }
    });
});
document.addEventListener('DOMContentLoaded', () => {
    const themeToggleButton = document.getElementById('theme-toggle');
    const currentTheme = localStorage.getItem('theme');

    if (currentTheme === 'dark') {
        document.body.classList.add('dark-theme');
    }

    themeToggleButton.addEventListener('click', () => {
        document.body.classList.toggle('dark-theme');
        const isDarkTheme = document.body.classList.contains('dark-theme');
        localStorage.setItem('theme', isDarkTheme ? 'dark' : 'light');
    });
});
