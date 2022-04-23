import validators
import keyboard
from main import OzonParser, WildberriesParser
from selenium.common.exceptions import NoSuchWindowException, WebDriverException


def main():
    # starting program
    print("Starting service...")
    while True:
        print("Please, type full url (https://...) of site/category/product to run parser: ")
        address = input()
        if validators.url(address):
            # site check
            try:
                if 'ozon' in address:
                    Ozon = OzonParser()
                    if 'category' in address or 'highlight' in address:
                        # category url
                        Ozon.parse_category(address)
                    elif 'product' in address:
                        # item url
                        data = Ozon.get_item_info(address)
                        OzonParser.json_item_backup(data)
                    else:
                        # site url
                        Ozon.parse_site()
                elif 'wildberries' in address:
                    wb = WildberriesParser()
                    if 'catalog' in address:
                        # category url
                        wb.parse_category(address)
                    elif 'detail.aspx' in address:
                        # item url
                        data = WildberriesParser.get_item_info(address)
                        wb.json_item_backup(data)
                    else:
                        # site url
                        wb.parse_site()
                else:
                    print("This site has not supported yet! Parser can process only 'Ozon' and 'Wildberries'.")
            except NoSuchWindowException:
                print("The parser window was closed!")
            print("Press any key to continue or press 'ESC' to exit: ")
            if keyboard.read_key() == 'esc':
                break
        else:
            print('Got invalid url! Please, type again...')
    print("Stopping service...")
    exit(0)


if __name__ == '__main__':
    main()
