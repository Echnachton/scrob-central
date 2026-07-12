from dotenv import load_dotenv
from controller import register_routes

load_dotenv()

def main():
    register_routes()
    print("Hello from scrob-central!")


if __name__ == "__main__":
    main()
