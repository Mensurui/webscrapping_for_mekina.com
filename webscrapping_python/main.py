import asyncio
from prisma import Prisma
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

async def scrape_cars_data() -> None:
    db = Prisma()
    await db.connect()
    all_cars = []
    base_url = "https://www.mekina.net/cars/?body_type=Sedan&page="

    for page_number in range(1, 4):
        res = requests.get(base_url + str(page_number))
        soup = BeautifulSoup(res.text, 'lxml')

        cars = soup.find_all('div', class_='category-grid-box-1')
        for car in cars:
            car_name = car.find('h3').text.strip()
            car_price = car.find('div', class_='price').text.strip()
            car_more_info = car.h3.a['href'].strip()
            car_posted = car.find('ul', class_='list-unstyled').text.strip()
            car_plate = car.find('p', class_='location').text.strip()
            posted_time = parse_posted_time(car_posted)
            
            if 'Toyota' in car_name and is_posted_within_last_week(posted_time):
                all_cars.append({'Name': car_name, 'Price': car_price, 'More Info': car_more_info, "Posted": car_posted, "Plate": car_plate})
                car = await db.car.create({
                    'name': car_name,
                    'price': car_price,
                    'more_info': car_more_info,
                    'posted': car_posted,
                    'plate': car_plate
                })
                print(f'created post: {car.model_dump_json(indent=2)}')

    await db.disconnect()  # Close the database connection after processing all cars

    return all_cars

def parse_posted_time(posted_time_str):
    if 'hour' in posted_time_str:
        hours_ago = int(posted_time_str.split()[0])
        return datetime.now() - timedelta(hours=hours_ago)
    elif 'week' in posted_time_str:
        days_ago = int(posted_time_str.split()[0]) * 7
        return datetime.now() - timedelta(days=days_ago)
    # Handle cases where posted time is not specified
    else:
        return datetime.now()

def is_posted_within_last_week(posted_time):
    one_week_ago = datetime.now() - timedelta(weeks=1)
    return posted_time > one_week_ago

if __name__ == '__main__':
    asyncio.run(scrape_cars_data())
