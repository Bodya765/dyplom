document.addEventListener('DOMContentLoaded', () => {
  const preloader = document.getElementById('preloader');

  // Ховаємо прелоадер після повного завантаження сторінки
  window.addEventListener('load', () => {
    setTimeout(() => {
      preloader.classList.add('hidden');
      // Видаляємо прелоадер із DOM після завершення анімації
      setTimeout(() => preloader.remove(), 500);
    }, 500); // Затримка перед зникненням (0.5 секунди)
  });

  // Альтернатива: ховаємо через 2 секунди, якщо завантаження швидке
  setTimeout(() => {
    preloader.classList.add('hidden');
    setTimeout(() => preloader.remove(), 300);
  }, 400);
});