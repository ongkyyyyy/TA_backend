const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const axios = require('axios');

puppeteer.use(StealthPlugin());

async function scrapeReviews(hotelUrl, retryAttempt = 0) {
    const MAX_RETRIES = 3;

    if (!hotelUrl) {
        console.error("Error: No hotel URL provided.");
        return;
    }

    console.log(`Launching Puppeteer (Attempt ${retryAttempt + 1})...`);
    const browser = await puppeteer.launch({ 
        headless: "new",  
        defaultViewport: null, 
        args: ["--start-maximized"] 
    });

    try {
        const page = await browser.newPage();
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36');

        console.log(`Opening the hotel page: ${hotelUrl}`);
        await page.goto(hotelUrl, { waitUntil: 'domcontentloaded' });

        const hotelName = await page.evaluate(() => {
            const hotelNameElem = document.querySelector('[data-testid="display_name_label"]');
            return hotelNameElem ? hotelNameElem.innerText.trim() : 'Unknown Hotel';
        });

        console.log(`Hotel Name: ${hotelName}`);

        let allReviews = [];
        let pageCounter = 1;

        while (true) {
            console.log(`Scraping page ${pageCounter}...`);
            await new Promise(resolve => setTimeout(resolve, 3000));

            const reviews = await page.evaluate((hotelName) => {
                return Array.from(document.querySelectorAll('.css-1dbjc4n.r-14lw9ot.r-h1746q.r-kdyh1x.r-d045u9.r-18u37iz.r-1fdih9r.r-1udh08x.r-d23pfw')).map(review => {
                    const usernameElem = review.querySelector('[data-testid="reviewer-name"]');
                    const ratingElem = review.querySelector('[data-testid="tvat-ratingScore"]');
                    const commentElem = review.querySelector('.css-901oao.css-cens5h');

                    const timestampElem = Array.from(review.querySelectorAll("div.css-901oao"))
                        .find(div => div.innerText.match(/\d{1,2} \w{3,} \d{4}/));
                    const timestampText = timestampElem ? timestampElem.innerText.trim() : 'Unknown Date';

                    return {
                        username: usernameElem ? usernameElem.innerText.trim() : 'Anonymous',
                        rating: ratingElem ? parseFloat(ratingElem.innerText.trim().replace(',', '.')) : null,
                        comment: commentElem && commentElem.innerText.trim() ? commentElem.innerText.trim() : '-',
                        timestamp: timestampText,
                        hotel_name: hotelName,
                        OTA: 'Traveloka'
                    };
                }).filter(review => review.comment && review.rating !== null && review.rating > 0);
            }, hotelName);

            for (const review of reviews) {
                const yearMatch = review.timestamp.match(/\d{4}/);
                if (yearMatch) {
                    const year = parseInt(yearMatch[0], 10);
                    if (year < 2024) {
                        console.log("Encountered 2023 or earlier review. Stopping scraping.");
                        console.log("Total Reviews Scraped:", allReviews.length);
                        await sendReviews(allReviews);
                        console.log("Closing browser...");
                        await browser.close();
                        return;
                    }
                }
                allReviews.push(review);
            }

            console.log(`Collected ${reviews.length} reviews from page ${pageCounter}.`);

            const nextPageButton = await page.$('img[src*="ff1bf47098bb677fe4ba66933f585fab.svg"]');
            if (!nextPageButton) {
                console.log("No more pages to scrape.");
                break;
            }

            const isDisabled = await page.evaluate(button => {
                return button.closest('div[role="button"]').getAttribute('aria-disabled') === "true";
            }, nextPageButton);

            if (isDisabled) {
                console.log("Next page button is disabled. Stopping pagination.");
                break;
            }

            console.log("Navigating to the next page...");
            await nextPageButton.click();
            await new Promise(resolve => setTimeout(resolve, 3000));
            pageCounter++;
        }

        console.log("Total Reviews Scraped:", allReviews.length);
        await sendReviews(allReviews);
    } catch (err) {
        console.error(`❌ Error during scraping: ${err.message}`);
        await browser.close();
        if (retryAttempt + 1 < MAX_RETRIES) {
            console.log("🔁 Retrying scrape...");
            await new Promise(resolve => setTimeout(resolve, 5000));
            return scrapeReviews(hotelUrl, retryAttempt + 1);
        } else {
            console.error("❌ Max retry attempts reached. Giving up.");
        }
        return;
    }

    console.log("Closing browser...");
    await browser.close();
}

async function sendReviews(reviews) {
    try {
        if (reviews.length > 0) {
            await axios.post('http://127.0.0.1:5000/reviews', { reviews });
            console.log('✅ Data sent to backend successfully');
        } else {
            console.log('ℹ️ No valid reviews found.');
        }
    } catch (error) {
        console.error('❌ Error sending data:', error.message);
    }
}

const hotelUrl = process.argv[2]; 
scrapeReviews(hotelUrl);
