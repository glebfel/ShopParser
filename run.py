import validators
from main import OzonParser


def main():
    # starting program
    print("Strating servece...")
    print("Please, type url of site/category/product to run parser: ")
    while True:
        address = input()
        if validators.url(address):
            # site check
            Ozon = OzonParser()
            if 'ozon' in address:
                if 'category' in address:
                    # category url
                    Ozon.parse_category(address)
                elif 'product' in address:
                    # item url
                    data = Ozon.get_item_info(address)
                    OzonParser.json_item_backup(data)
                else:
                    # site url
                    Ozon.parse_site()
        else:
            print('Got invalid url. Please, type again...')
    print("Stoping servece...")


if __name__ == '__main__':
    main()
