/**************************************
    File Name: custom.js
    Template Name: Forest Time
    Created By: HTML.Design
    http://themeforest.net/user/wpdestek
**************************************/

(function($) {
    "use strict";

    $(document).ready(function() {
        // ১. নেভিগেশন এক্সপ্যান্ডার
        $('#nav-expander').on('click', function(e) {
            e.preventDefault();
            $('body').toggleClass('nav-expanded');
        });
        $('#nav-close').on('click', function(e) {
            e.preventDefault();
            $('body').removeClass('nav-expanded');
        });

        // ২. বুটস্ট্র্যাপ টুলটিপ
        if ($.fn.tooltip) {
            $('[data-toggle="tooltip"]').tooltip();
        }

        // ৩. ক্যারোসেল ইন্টারভ্যাল
        if ($.fn.carousel) {
            $('.carousel').carousel({
                interval: 4000
            });
        }

        // ৪. Scroll to Top (dmtop) ফাংশনালিটি
        $(window).scroll(function() {
            if ($(this).scrollTop() > 1) {
                $('.dmtop').css({ bottom: "25px" });
            } else {
                $('.dmtop').css({ bottom: "-100px" });
            }
        });

        $('.dmtop').click(function() {
            $('html, body').animate({ scrollTop: '0px' }, 800);
            return false;
        });
    });

    // ৫. প্রিলোডার হ্যান্ডলিং
    $(window).on('load', function() {
        $("#preloader").fadeOut(500);
        $(".preloader").fadeOut("slow");
    });

})(jQuery);

// ৬. ক্যাটাগরি ট্যাব ফাংশন (Vanilla JS)
function openCategory(evt, catName) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    var targetTab = document.getElementById(catName);
    if (targetTab) {
        targetTab.style.display = "block";
        evt.currentTarget.className += " active";
    }
}

// ৭. ব্লগ কন্টেন্ট অটোমেশন (TOC, Amazon Links, Image Styling)
document.addEventListener("DOMContentLoaded", function() {
    const postBody = document.querySelector('.blog-content');
    if (!postBody) return;

    const headers = postBody.querySelectorAll('h2, h3');

    // ১. Table of Contents (TOC) অটোমেশন
    if (headers.length >= 2) {
        let tocHTML = `
            <div id="dynamic-toc" class="widget" style="border: 1px solid #e1e1e1; padding: 20px; border-radius: 8px; margin: 30px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; cursor: pointer;" id="toc-header">
                    <span style="font-weight: bold; font-size: 1.2em; color: inherit;">Table of Contents</span>
                    <span id="toc-toggle-icon" style="color: #28a745;">[+] Show</span>
                </div>
                <div id="toc-list-container" style="display: none; margin-top: 15px; border-top: 1px solid #ddd; padding-top: 15px;">
                    <ul id="toc-links" style="padding-left: 20px; line-height: 1.8; list-style-type: decimal; color: inherit;"></ul>
                </div>
            </div>
        `;
        
        const firstP = postBody.querySelector('p');
        if (firstP) {
            firstP.insertAdjacentHTML('afterend', tocHTML);
        }

        const tocLinks = document.getElementById('toc-links');
        headers.forEach((h, i) => {
            const id = 'section-' + i;
            h.setAttribute('id', id);
            const li = document.createElement('li');
            if (h.tagName === 'H3') li.style.marginLeft = "20px";
            li.innerHTML = `<a href="#${id}" style="color: #28a745; text-decoration: none; font-weight: 500;">${h.textContent}</a>`;
            tocLinks.appendChild(li);
        });

        const tocHeader = document.getElementById('toc-header');
        if (tocHeader) {
            tocHeader.onclick = function() {
                const list = document.getElementById('toc-list-container');
                const icon = document.getElementById('toc-toggle-icon');
                const isHidden = list.style.display === "none";
                list.style.display = isHidden ? "block" : "none";
                icon.innerText = isHidden ? "[-] Hide" : "[+] Show";
            };
        }
    }

    // ২. Amazon লিংকে অটোমেটিক 'nofollow sponsored' যোগ করা
    const links = postBody.querySelectorAll('a');
    links.forEach(link => {
        if (link.href.includes('amazon.com') || link.href.includes('amzn.to')) {
            link.setAttribute('rel', 'nofollow sponsored');
            link.setAttribute('target', '_blank');
        }
    });

    // ৩. কন্টেন্ট ইমেজে লেজি লোডিং এবং স্টাইল যুক্ত করা
    const bodyImages = postBody.querySelectorAll('img');
    bodyImages.forEach(img => {
        img.setAttribute('loading', 'lazy'); 
        img.style.maxWidth = "100%";
        img.style.height = "auto";
        img.style.boxShadow = "0 4px 12px rgba(0,0,0,0.1)";
        img.style.border = "1px solid #eee";
        img.style.borderRadius = "8px";
        img.style.margin = "20px 0";
    });
});


// Dark Mode Logic
document.addEventListener('DOMContentLoaded', function () {
    const darkModeToggle = document.getElementById('darkModeToggle');
    const savedDark = localStorage.getItem('darkMode') === 'true';
    if (savedDark) {
        document.body.classList.add('dark-mode');
    }

    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function () {
            document.body.classList.toggle('dark-mode');
            const isDark = document.body.classList.contains('dark-mode');
            localStorage.setItem('darkMode', isDark);
        });
    }
});


//*********** স্ক্রল বাটন ফিক্সড শুরু **************

// একটি কমন নাম ব্যবহার করা হলো যাতে Conflict না হয়
const mySmartScrollBtn = document.getElementById("smart-scroll-top") || document.getElementById("scrollBtn");

if (mySmartScrollBtn) {
    // ১. স্ক্রলে শো/হাইড লজিক
    window.addEventListener("scroll", function () {
        if (document.documentElement.scrollTop > 200 || document.body.scrollTop > 200) {
            mySmartScrollBtn.style.display = "flex";
        } else {
            mySmartScrollBtn.style.display = "none";
        }
    });

    // ২. ক্লিক করলে টপে স্ক্রল লজিক
    mySmartScrollBtn.addEventListener("click", function () {
        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });
    });

    // ৩. ড্র্যাগ লজিক
    let isDragging = false;
    let startX, startY, startLeft, startTop;

    mySmartScrollBtn.addEventListener("mousedown", function (e) {
        isDragging = true;
        mySmartScrollBtn.style.transition = "none";

        startX = e.clientX;
        startY = e.clientY;

        const rect = mySmartScrollBtn.getBoundingClientRect();
        startLeft = rect.left;
        startTop = rect.top;

        mySmartScrollBtn.style.left = startLeft + "px";
        mySmartScrollBtn.style.top = startTop + "px";
        mySmartScrollBtn.style.right = "auto";
        mySmartScrollBtn.style.bottom = "auto";
        mySmartScrollBtn.style.position = "fixed";

        const onMouseMove = (e) => {
            if (!isDragging) return;
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            mySmartScrollBtn.style.left = startLeft + dx + "px";
            mySmartScrollBtn.style.top = startTop + dy + "px";
        };

        const onMouseUp = () => {
            isDragging = false;
            mySmartScrollBtn.style.transition = "transform 0.15s";
            document.removeEventListener("mousemove", onMouseMove);
            document.removeEventListener("mouseup", onMouseUp);
        };

        document.addEventListener("mousemove", onMouseMove);
        document.addEventListener("mouseup", onMouseUp);
    });
}

//*********** স্ক্রল বাটন শেষ **************


// --- Subscription Notifications (HTMX + SweetAlert2) start ---

document.body.addEventListener('subscribed_success', function() {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: 'Successfully Subscribed!',
            text: 'Thank you for joining Forest Time community.',
            icon: 'success',
            confirmButtonText: 'Great!',
            confirmButtonColor: '#208957'
        });
    }
    
    const emailInput = document.querySelector('input[name="email"]');
    if (emailInput) emailInput.value = '';
});

document.body.addEventListener('already_subscribed', function() {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: 'Notice',
            text: 'This email is already subscribed!',
            icon: 'info',
            confirmButtonText: 'Okay'
        });
    }
});

// --- Subscription Notifications (HTMX + SweetAlert2) end ---