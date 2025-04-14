const deleteButton = document.getElementById("open-delete-modal");
const modal = document.getElementById("delete-modal");
const cancelButton = document.querySelector(".btn-cancel");
const deleteForm = document.getElementById("delete-form");

if (deleteButton) {
    deleteButton.addEventListener("click", function () {
        modal.style.display = "flex";
        deleteForm.action = "{% url 'announcements:delete_announcement' announcement.id %}";
    });
}

if (cancelButton) {
    cancelButton.addEventListener("click", function () {
        modal.style.display = "none";
    });
}

document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
        modal.style.display = "none";
    }
});
