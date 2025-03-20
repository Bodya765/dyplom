document.addEventListener("DOMContentLoaded", function () {
    const profilePhoto = document.getElementById("profilePhoto");
    const dropdownMenu = document.getElementById("dropdownMenu");

    if (profilePhoto && dropdownMenu) {
        // Toggle visibility when the profile photo is clicked
        profilePhoto.addEventListener("click", function(event) {
            event.preventDefault();
            dropdownMenu.classList.toggle("visible");
        });

        // Hide the dropdown if you click anywhere outside of it
        document.addEventListener("click", function(event) {
            if (!profilePhoto.contains(event.target) && !dropdownMenu.contains(event.target)) {
                dropdownMenu.classList.remove("visible");
            }
        });
    }
});
