from account.models import Account, User
import random
import pyfiglet

def init_db():
    try:
        if not User.objects.all().exists():
            user = User.objects.create(full_name = 'Super Admin')

            Account.objects.create(
                username = 'admin@gmail.com',
                user = user,
                password = '1'
            )

            # user.educations.set([1])
            print("Created Super Admin")
        
    except Exception as e:
        print(e)

def service_message(text):
    # Danh sách các kiểu chữ Figlet có sẵn
    fonts = pyfiglet.FigletFont.getFonts()

    list_fonts = ['graceful', 'clb8x8', 'war_of_w', 'ttyb', 'alphabet', 'times', 'small', 'fourtops', 'calgphy2', 'graffiti', 'charact6']

    # Chọn ngẫu nhiên một kiểu chữ từ danh sách
    random_font = random.choice(fonts)
    print("============ FONT ============")
    print(f"============ {random_font} ===========")

    # Tạo đối tượng Figlet với kiểu chữ ngẫu nhiên
    figlet = pyfiglet.Figlet(font=random_font)

    # Sinh ra chuỗi chữ kiểu Figlet
    ascii_art = figlet.renderText(text)

    return ascii_art
