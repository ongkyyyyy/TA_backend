const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const axios = require('axios');

puppeteer.use(StealthPlugin());

async function scrapeReviews(hotelUrl) {
    if (!hotelUrl) {
        console.error("Error: No hotel URL provided.");
        return;
    }

    console.log("Launching Puppeteer with Stealth Plugin...");
    const browser = await puppeteer.launch({ 
        headless: false,  
        defaultViewport: null, 
        args: [
            "--start-maximized",
            "--disable-notifications", 
            "--disable-infobars", 
            "--disable-popup-blocking"
        ] 
    });

    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36');

    page.on('dialog', async dialog => {
        console.log(`Dismissing popup: ${dialog.message()}`);
        await dialog.dismiss();
    });

    console.log(`Opening the hotel page: ${hotelUrl}`);
    await page.goto(hotelUrl, { waitUntil: 'domcontentloaded' });

    await new Promise(resolve => setTimeout(resolve, 2000));

    const hotelNameSelector = 'h1[class^="headInit_headInit-title_name"]';

        await page.waitForSelector(hotelNameSelector, { timeout: 2000 });

        await page.click(hotelNameSelector);
        console.log('Clicked the hotel name element once');

        await new Promise(resolve => setTimeout(resolve, 1000));

        const hotelName = await page.evaluate((selector) => {
            const hotelNameElem = document.querySelector(selector);
            return hotelNameElem ? hotelNameElem.innerText.trim() : 'Unknown Hotel';
        }, hotelNameSelector);

        console.log(`Hotel Name: ${hotelName}`);

    await new Promise(resolve => setTimeout(resolve, 1000));

    try {
        await page.waitForFunction(() => {
            const buttons = Array.from(document.querySelectorAll('button'));
            return buttons.some(btn => btn.textContent.includes('All reviews') || btn.textContent.includes('Semua ulasan'));
        }, { timeout: 8000 });
    
        await page.evaluate(() => {
            const buttons = Array.from(document.querySelectorAll('button'));
            const target = buttons.find(btn => 
                btn.textContent.includes('All reviews') || btn.textContent.includes('Semua ulasan')
            );
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                target.click();
            }
        });
    
        console.log('✅ Clicked the "All reviews" / "Semua ulasan" button');
        await new Promise(resolve => setTimeout(resolve, 2000));
    } catch (err) {
        console.error('❌ Failed to click "All reviews" button:', err.message);
    }    

    await new Promise(resolve => setTimeout(resolve, 2000));

        try {
            await page.waitForSelector('li.ceOnXE_xI6aGRTgG_wCS', { timeout: 10000 });
        
            const clicked = await page.evaluate(() => {
                const items = Array.from(document.querySelectorAll('li.ceOnXE_xI6aGRTgG_wCS span'));
                for (const item of items) {
                    const text = item.innerText.trim().toLowerCase();
                    if (text === 'most recent' || text === 'terbaru') {
                        item.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        item.click();
                        return true;
                    }
                }
                return false;
            });
        
            if (clicked) {
                console.log('✅ Selected "Most Recent" or "Terbaru" from sort options');
            } else {
                console.warn('⚠️ Could not find the "Most Recent" or "Terbaru" option to click');
            }
        
            await new Promise(resolve => setTimeout(resolve, 3000));
        } catch (error) {
            console.error('❌ Failed to click on sort option:', error.message);
        }   

    let allReviews = [];
    let pageCounter = 1;
    let lastReviewText = "";
    let retryAttempt = 0;

    while (true) {
        console.log(`Scraping page ${pageCounter}...`);
        await new Promise(resolve => setTimeout(resolve, 3000)); 

        let reviews = [];

        try {
            await page.waitForSelector('div.drawer_drawerContainer__6G_8M', { timeout: 10000 });
            console.log("✅ Review drawer detected");
        
            // Optional: take screenshot for debugging
            await page.screenshot({ path: `debug_drawer_${pageCounter}.png`, fullPage: true });
        
            // Scroll drawer to load content
            await page.evaluate(async () => {
                const drawer = document.querySelector('div.drawer_drawerContainer__6G_8M');
                if (drawer) {
                    drawer.scrollTop = drawer.scrollHeight;
                    await new Promise(resolve => setTimeout(resolve, 2000));
                }
            });
        
            // Log how many reviews are found inside the drawer
            const reviewCount = await page.evaluate(() => {
                const container = document.querySelector('div.drawer_drawerContainer__6G_8M');
                return container ? container.querySelectorAll('div.yRvZgc0SICPUbmdb2L2a').length : 0;
            });
            console.log(`Found ${reviewCount} review elements on page ${pageCounter}`);
        
            if (reviewCount === 0) {
                throw new Error("No reviews loaded in drawer");
            }
        
            // Now extract
            reviews = await page.evaluate((hotelName) => {
                const container = document.querySelector('div.drawer_drawerContainer__6G_8M');
                if (!container) return [];
            
                return Array.from(container.querySelectorAll('div.yRvZgc0SICPUbmdb2L2a')).map(review => {
                    const usernameElem = review.querySelector('.yCIHzFRsP6Tzk7Kia6Qo');
                    const ratingElem = review.querySelector('.xt_R_A70sdDRsOgExJWw');
                    const commentElem = review.querySelector('.UXjSnokalMIS5CzMtLSM');
                    const timestampElem = review.querySelector('.LPPTO8g2RH0Fk19jYMOQ');
            
                    return {
                        username: usernameElem ? usernameElem.innerText.trim() : 'Anonymous',
                        rating: ratingElem ? parseFloat(ratingElem.innerText.trim().replace(',', '.')) : null,
                        comment: commentElem && commentElem.innerText.trim() ? commentElem.innerText.trim() : '-',
                        timestamp: timestampElem ? timestampElem.innerText.trim() : 'Unknown Date',
                        hotel_name: hotelName,
                        OTA: 'Trip.com'
                    };
                }).filter(review => review.comment && review.rating !== null && review.rating > 0);
            }, hotelName); // ← don't forget to pass it here
            
        } catch (err) {
            console.log("❌ Error during review extraction:", err.message);
            retryAttempt++;
            if (retryAttempt >= 3) {
                console.log("❌ Maximum retry attempts reached. Stopping.");
                break;
            }
            continue;
        }

        if (reviews.length > 0 && reviews[0].comment === lastReviewText) {
            console.log("⚠️ Detected repeated review page. Retrying...");
            retryAttempt++;
            if (retryAttempt >= 3) {
                console.log("❌ Maximum retry attempts due to repetition reached. Stopping.");
                break;
            }
            continue;
        } else {
            retryAttempt = 0;
            lastReviewText = reviews.length > 0 ? reviews[0].comment : lastReviewText;
        }

        let foundOldReview = false;

        for (const review of reviews) {
            const [day, month, year] = review.timestamp.split('-').map(val => parseInt(val, 10));
            if (year < 24) {
                console.log("Encountered 2023 or earlier review. Stopping scraping.");
                await sendReviews(allReviews);
                await browser.close();
                return;
            }
            allReviews.push(review);
        }

        console.log(`Collected ${reviews.length} reviews from page ${pageCounter}.`);

        if (foundOldReview) {
            console.log("Total Reviews Scraped:", allReviews.length);
            await sendReviews(allReviews);
            console.log("Closing browser...");
            await browser.close();
            return;
        }

        const nextPageButton = await page.$('li.nF6SWkdU6FLIzjoCbLMF.KtjTmkGBZvROMSO8zK_Q > a.pQoxbX5l0DdjPttuVUQx');

        if (!nextPageButton) {
            console.log("❌ No 'Next Page' button found. Ending scraping.");
            break;
        }

        const isDisabled = await page.evaluate(button => {
            const parentLi = button.closest('li');
            return parentLi && parentLi.classList.contains('disabled');
        }, nextPageButton);

        if (isDisabled) {
            console.log("❌ 'Next Page' button is disabled. Stopping pagination.");
            break;
        }

        console.log("Navigating to the next page...");
        await nextPageButton.click();

        await new Promise(resolve => setTimeout(resolve, 3000));
        pageCounter++;
    }     

    console.log("Total Reviews Scraped:", allReviews.length);
    await sendReviews(allReviews);
    console.log("Closing browser...");
    await browser.close();
}

async function sendReviews(reviews) {
    try {
        if (reviews.length > 0) {
            await axios.post('http://127.0.0.1:5000/reviews', { reviews });
            console.log('Data sent to backend successfully');
        } else {
            console.log('No valid reviews found.');
        }
    } catch (error) {
        console.error('Error sending data:', error.message);
    }
}

const hotelUrl = process.argv[2]; 
scrapeReviews(hotelUrl);
