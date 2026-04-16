document.addEventListener("DOMContentLoaded", () => {
    const flashMessages = document.querySelectorAll(".flash");

    flashMessages.forEach((message) => {
        window.setTimeout(() => {
            message.style.opacity = "0";
            message.style.transform = "translateY(-6px)";
            message.style.transition = "0.3s ease";
        }, 3000);
    });

    const slider = document.querySelector("[data-slider]");
    if (slider) {
        const slides = Array.from(slider.querySelectorAll(".promo-slide"));
        const dots = Array.from(slider.querySelectorAll(".slider-dot"));
        const prevButton = slider.querySelector("[data-slider-prev]");
        const nextButton = slider.querySelector("[data-slider-next]");

        let activeIndex = 0;
        let intervalId = null;

        const renderSlider = (index) => {
            slides.forEach((slide, slideIndex) => {
                slide.classList.toggle("is-active", slideIndex === index);
            });

            dots.forEach((dot, dotIndex) => {
                dot.classList.toggle("is-active", dotIndex === index);
            });
        };

        const goToSlide = (index) => {
            activeIndex = (index + slides.length) % slides.length;
            renderSlider(activeIndex);
        };

        const startAutoPlay = () => {
            intervalId = window.setInterval(() => {
                goToSlide(activeIndex + 1);
            }, 4500);
        };

        const resetAutoPlay = () => {
            if (intervalId) {
                window.clearInterval(intervalId);
            }
            startAutoPlay();
        };

        prevButton?.addEventListener("click", () => {
            goToSlide(activeIndex - 1);
            resetAutoPlay();
        });

        nextButton?.addEventListener("click", () => {
            goToSlide(activeIndex + 1);
            resetAutoPlay();
        });

        dots.forEach((dot, index) => {
            dot.addEventListener("click", () => {
                goToSlide(index);
                resetAutoPlay();
            });
        });

        renderSlider(activeIndex);
        startAutoPlay();
    }

    const offersScroller = document.querySelector("[data-offers-scroller]");
    const offersPrev = document.querySelector("[data-offers-prev]");
    const offersNext = document.querySelector("[data-offers-next]");

    if (offersScroller) {
        const scrollAmount = () => Math.min(340, offersScroller.clientWidth * 0.9);

        offersPrev?.addEventListener("click", () => {
            offersScroller.scrollBy({ left: -scrollAmount(), behavior: "smooth" });
        });

        offersNext?.addEventListener("click", () => {
            offersScroller.scrollBy({ left: scrollAmount(), behavior: "smooth" });
        });
    }

    const cartDrawer = document.querySelector("[data-cart-drawer]");
    const cartOverlay = document.querySelector("[data-cart-overlay]");
    const cartOpenButtons = document.querySelectorAll("[data-cart-open]");
    const cartCloseButtons = document.querySelectorAll("[data-cart-close]");
    const quickToast = document.querySelector("[data-quick-toast]");

    const setCartState = (isOpen) => {
        cartDrawer?.classList.toggle("is-open", isOpen);
        cartOverlay?.classList.toggle("is-open", isOpen);
        document.body.classList.toggle("drawer-open", isOpen);
    };

    cartOpenButtons.forEach((button) => {
        button.addEventListener("click", () => setCartState(true));
    });

    cartCloseButtons.forEach((button) => {
        button.addEventListener("click", () => setCartState(false));
    });

    cartOverlay?.addEventListener("click", () => setCartState(false));

    const wishlistForms = document.querySelectorAll("[data-wishlist-form]");
    wishlistForms.forEach((form) => {
        form.addEventListener("submit", async (event) => {
            event.preventDefault();

            const button = form.querySelector("[data-wishlist-button]");
            const formData = new FormData(form);

            try {
                const response = await fetch(form.action, {
                    method: "POST",
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    body: formData,
                });

                const data = await response.json();
                if (!response.ok || !data.success) {
                    return;
                }

                if (data.is_favorite) {
                    button?.classList.add("is-saved");
                    if (button) {
                        button.innerHTML = "&#10084;";
                    }
                    if (quickToast) {
                        quickToast.textContent = "Added to favourites";
                        quickToast.classList.add("is-visible");
                        window.clearTimeout(window.zmartToastTimeout);
                        window.zmartToastTimeout = window.setTimeout(() => {
                            quickToast.classList.remove("is-visible");
                        }, 1800);
                    }
                } else {
                    button?.classList.remove("is-saved");
                    if (button) {
                        button.innerHTML = "&#9825;";
                    }

                    if (quickToast) {
                        quickToast.textContent = "Removed from favourites";
                        quickToast.classList.add("is-visible");
                        window.clearTimeout(window.zmartToastTimeout);
                        window.zmartToastTimeout = window.setTimeout(() => {
                            quickToast.classList.remove("is-visible");
                        }, 1800);
                    }

                    if (window.location.pathname === "/favorites") {
                        const card = form.closest(".product-card");
                        card?.remove();
                    }
                }
            } catch (error) {
                console.error("Wishlist update failed", error);
            }
        });
    });

    const assistantForm = document.querySelector("[data-assistant-form]");
    const assistantResults = document.querySelector("[data-assistant-results]");
    const assistantPromptInput = document.querySelector("#assistant-prompt");
    const assistantPromptButtons = document.querySelectorAll("[data-assistant-prompt]");

    const renderAssistantResult = (data) => {
        if (!assistantResults) {
            return;
        }

        const summaryMarkup = data.summary
            ? `<span class="assistant-summary">${data.summary}</span>`
            : "";

        const recommendationsMarkup = (data.recommendations || []).length
            ? `<div class="assistant-recommendation-grid">
                ${data.recommendations.map((product) => `
                    <article class="assistant-product-card">
                        <span class="chip">${product.category}</span>
                        <h3>${product.name}</h3>
                        <p>Rs. ${product.price} · ${product.stock_quantity} in stock</p>
                        <a href="/product/${product.product_id}" class="btn btn-secondary btn-small">View Product</a>
                    </article>
                `).join("")}
               </div>`
            : `<div class="assistant-empty-state"><strong>No product suggestions found.</strong><p>Try another shopping request.</p></div>`;

        assistantResults.innerHTML = `
            <div class="assistant-response-card">
                <strong>Assistant Reply</strong>
                <p>${data.reply}</p>
                ${summaryMarkup}
            </div>
            ${recommendationsMarkup}
        `;
    };

    assistantPromptButtons.forEach((button) => {
        button.addEventListener("click", () => {
            if (assistantPromptInput) {
                assistantPromptInput.value = button.getAttribute("data-assistant-prompt") || "";
                assistantPromptInput.focus();
            }
        });
    });

    assistantForm?.addEventListener("submit", async (event) => {
        event.preventDefault();

        if (!assistantPromptInput || !assistantResults) {
            return;
        }

        const prompt = assistantPromptInput.value.trim();
        if (!prompt) {
            return;
        }

        assistantResults.innerHTML = `
            <div class="assistant-response-card">
                <strong>Thinking...</strong>
                <p>Looking through the current inventory for the best matches.</p>
            </div>
        `;

        try {
            const response = await fetch("/api/ai-assistant", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ prompt }),
            });

            const data = await response.json();
            renderAssistantResult(data);
        } catch (error) {
            assistantResults.innerHTML = `
                <div class="assistant-response-card">
                    <strong>Assistant unavailable</strong>
                    <p>Something went wrong while fetching suggestions. Please try again.</p>
                </div>
            `;
        }
    });
});
