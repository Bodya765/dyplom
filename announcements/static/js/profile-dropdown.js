document.addEventListener("DOMContentLoaded", function () {
    const profilePhoto = document.getElementById("profilePhoto");
    const dropdownMenu = document.getElementById("dropdownMenu");

    if (profilePhoto && dropdownMenu) {
        profilePhoto.addEventListener("click", function(event) {
            event.preventDefault();
            event.stopPropagation();
            const isVisible = dropdownMenu.classList.toggle("show");
            profilePhoto.setAttribute("aria-expanded", isVisible ? "true" : "false");
        });

        document.addEventListener("click", function(event) {
            if (!profilePhoto.contains(event.target) && !dropdownMenu.contains(event.target)) {
                dropdownMenu.classList.remove("show");
                profilePhoto.setAttribute("aria-expanded", "false");
            }
        });

        dropdownMenu.addEventListener("click", function(event) {
            event.stopPropagation();
        });

        document.addEventListener("keydown", function(event) {
            if (event.key === "Escape") {
                dropdownMenu.classList.remove("show");
                profilePhoto.setAttribute("aria-expanded", "false");
            }
        });
    }
});
