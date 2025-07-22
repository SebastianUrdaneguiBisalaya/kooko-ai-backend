# kooko.ai

> Back-end for **kooko.ai**

> Developed by [Sebastian Marat Urdanegui Bisalaya](https://sebastianurdanegui.vercel.app)

> This backend component powers the **kooko.ai** platform by providing the data recognition and structuring capabilities. It consists of a Telegram Bot that leverages Google Gemini for Optical Character Recognition (OCR) to extract data from receipts and invoices, and then strcutures this data according to predefined database table schemas.

## Technologies

- **Python:** The primary programming language used for the bot's logic.

- **Google Gemini:** Utilized for its advanced OCR capabilities to extract text from images of receipts and invoices.

- **Telegram Bot API:** Facilitates communication between the bot and Telegram users.

- **Supabase:** Serves as the database where the structured financial data is stored.

## Features

- **Receipt and Invoice Recognition:** Users can send images of receipts and invoices to the Telegram Bot.

- **Google Gemini OCR:** The bot employs Google Gemini to perform OCR on the received images, accurately extracting relevant data points.

- **Data Structuring:** Extracted data is meticulously structured to adhere to the predefined table schemas within the Supabase database, ensuring data consistency and integrity.

- **Automated Data Upload:** Recognized and structured data is automatically uploaded to the Supabase database, making it immediately available for the frontend application.

- **Seamless Integration:** Designed to work in conjunction with the **kooko.ai frontend**, providing the raw, processed data for visualization and analysis.