document.addEventListener("DOMContentLoaded", function () {
    const profilePhoto = document.getElementById("profilePhoto");
    const dropdownMenu = document.getElementById("dropdownMenu");

    if (profilePhoto && dropdownMenu) {
        profilePhoto.addEventListener("click", function(event) {
            event.preventDefault();
            dropdownMenu.classList.toggle("visible");  // Використовуємо клас для показу/приховування меню
        });
    }
});
