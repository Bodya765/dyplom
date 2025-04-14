document.addEventListener('DOMContentLoaded', () => {
  const fileLabel = document.querySelector('.file-label');
  const fileInput = document.querySelector('.file-input');
  const imagePreview = document.querySelector('.image-preview');
  const previewImg = document.querySelector('.preview-img');
  const modal = document.getElementById('imageModal');
  const modalImg = document.querySelector('.modal-img');
  const closeModal = document.querySelector('.close-modal');

  if (fileLabel && fileInput && imagePreview && previewImg) {
    fileLabel.addEventListener('click', () => {
      fileInput.click(); // Викликаємо вибір файлу
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files && fileInput.files[0]) {
        const reader = new FileReader();
        reader.onload = (e) => {
          previewImg.src = e.target.result;
          imagePreview.style.display = 'block'; // Показуємо прев’ю
          fileLabel.style.display = 'none'; // Ховаємо кнопку
        };
        reader.readAsDataURL(fileInput.files[0]);
      }
    });

    previewImg.addEventListener('click', () => {
      modalImg.src = previewImg.src;
      modal.style.display = 'flex'; // Показуємо модальне вікно
    });
  }

  if (closeModal && modal) {
    closeModal.addEventListener('click', () => {
      modal.style.display = 'none'; // Ховаємо модальне вікно
    });

    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.style.display = 'none'; // Закриття при кліку поза фото
      }
    });
  }
});