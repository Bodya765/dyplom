document.addEventListener("DOMContentLoaded", function () {
    const profilePhoto = document.getElementById("profilePhoto");
    const dropdownMenu = document.getElementById("dropdownMenu");

    if (profilePhoto && dropdownMenu) {
        // Відкриття/закриття меню при кліку на фото профілю
        profilePhoto.addEventListener("click", function(event) {
            event.preventDefault();
            event.stopPropagation(); // Остановить всплытие события
            const isVisible = dropdownMenu.classList.toggle("visible");
            profilePhoto.setAttribute("aria-expanded", isVisible ? "true" : "false");
        });

        // Закриття меню при кліку поза фото профілю або меню
        document.addEventListener("click", function(event) {
            if (!profilePhoto.contains(event.target) && !dropdownMenu.contains(event.target)) {
                dropdownMenu.classList.remove("visible");
                profilePhoto.setAttribute("aria-expanded", "false");
            }
        });

        // Запобігання закриттю меню при кліку всередині нього
        dropdownMenu.addEventListener("click", function(event) {
            event.stopPropagation(); // Щоб клік всередині меню не закривав його
        });

        // Закриття меню при натисканні клавіші ESC
        document.addEventListener("keydown", function(event) {
            if (event.key === "Escape") {
                dropdownMenu.classList.remove("visible");
                profilePhoto.setAttribute("aria-expanded", "false");
            }
        });
    }
});
