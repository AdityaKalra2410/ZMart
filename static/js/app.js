document.addEventListener("DOMContentLoaded", () => {
    const flashMessages = document.querySelectorAll(".flash");

    flashMessages.forEach((message) => {
        window.setTimeout(() => {
            message.style.opacity = "0";
            message.style.transform = "translateY(-6px)";
            message.style.transition = "0.3s ease";
        }, 3000);
    });
});
