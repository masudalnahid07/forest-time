document.addEventListener("DOMContentLoaded", function() {
    // ফিল্ডগুলোর আইডি ধরছি (জ্যাংগো সাধারণত id_field_name এভাবে আইডি তৈরি করে)
    const keywordInput = document.getElementById("id_focus_keyword");
    const contentField = document.getElementById("id_post_details");

    if (!keywordInput) return;

    // কাউন্ট দেখানোর জন্য একটি স্প্যান (span) তৈরি করে ইনপুটের পাশে বসাচ্ছি
    const countDisplay = document.createElement("span");
    countDisplay.style.fontWeight = "bold";
    countDisplay.style.marginLeft = "15px";
    countDisplay.style.fontSize = "14px";
    keywordInput.parentNode.appendChild(countDisplay);

    function updateKeywordCount() {
        let keyword = keywordInput.value.trim().toLowerCase();
        let content = "";

        // চেক করা হচ্ছে CKEditor আছে কি না
        if (typeof CKEDITOR !== "undefined" && CKEDITOR.instances["id_post_details"]) {
            // CKEditor থেকে টেক্সট নেওয়া
            let htmlContent = CKEDITOR.instances["id_post_details"].getData();
            let tempDiv = document.createElement("div");
            tempDiv.innerHTML = htmlContent;
            content = (tempDiv.textContent || tempDiv.innerText || "").toLowerCase();
        } else if (contentField) {
            // সাধারণ টেক্সটএরিয়া হলে
            content = contentField.value.toLowerCase();
        }

        if (keyword === "") {
            countDisplay.innerHTML = "⚠️ কোনো Focus Keyword দেওয়া হয়নি";
            countDisplay.style.color = "#ff9800"; // Orange
            return;
        }

        // কিওয়ার্ড কতবার আছে তা গোনা (Regex ব্যবহার করে)
        let escapedKeyword = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        // \b ব্যবহার করা হয়েছে যেন সম্পূর্ণ শব্দটি ম্যাচ করে
        let regex = new RegExp("\\b" + escapedKeyword + "\\b", "gi"); 
        let matches = content.match(regex);
        let count = matches ? matches.length : 0;

        // কাউন্টের ওপর ভিত্তি করে মেসেজ ও কালার পরিবর্তন
        if (count === 0) {
            countDisplay.innerHTML = `❌ আর্টিকেলে কিওয়ার্ডটি পাওয়া যায়নি (0 বার)`;
            countDisplay.style.color = "#dc3545"; // Red
        } else if (count > 0 && count < 3) {
            countDisplay.innerHTML = `⚠️ কিওয়ার্ডটি মাত্র ${count} বার আছে (আরও ব্যবহার করুন)`;
            countDisplay.style.color = "#ff9800"; // Orange
        } else {
            countDisplay.innerHTML = `✅ চমৎকার! কিওয়ার্ডটি ${count} বার ব্যবহার করা হয়েছে`;
            countDisplay.style.color = "#28a745"; // Green
        }
    }

    // কিওয়ার্ড ইনপুটে কিছু লিখলে সাথে সাথে আপডেট হবে
    keywordInput.addEventListener("keyup", updateKeywordCount);

    // সাধারণ টেক্সট এরিয়াতে লিখলে আপডেট হবে
    if (contentField) {
        contentField.addEventListener("keyup", updateKeywordCount);
    }

    // CKEditor এ লিখলে লাইভ আপডেট হবে
    if (typeof CKEDITOR !== "undefined") {
        CKEDITOR.on("instanceReady", function(event) {
            if (event.editor.name === "id_post_details") {
                event.editor.on("change", updateKeywordCount);
                event.editor.on("key", updateKeywordCount);
            }
        });
    }

    // পেজ লোড হওয়ার ১ সেকেন্ড পর প্রথমবার চেক করবে
    setTimeout(updateKeywordCount, 1000);
});