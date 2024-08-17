import sys
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QTableWidget, QTableWidgetItem, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QScreen
import yfinance as yf
import numpy as np


class StockApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("주식현재주가정보")
        self.setGeometry(100, 100, 800, 800)
        self.center_window()

        # 데이터 저장 및 로드
        self.data_file = "stock_data.json"
        self.load_data()

        # 메인 위젯과 레이아웃 설정
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # 타이틀 추가
        title_label = QLabel("Current Stock Status")
        # QSS에서 스타일 적용을 위해 ObjectName 설정
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 상단 입력 필드와 버튼 레이아웃
        input_layout = QHBoxLayout()

        self.ticker_input = QLineEdit(self)
        self.ticker_input.setPlaceholderText("틱커명")
        self.ticker_input.textChanged.connect(
            self.convert_to_uppercase)  # 대문자 변환
        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("종목명")
        self.price_1y_input = QLineEdit(self)
        self.price_1y_input.setPlaceholderText("1년 전 가격")
        self.price_6m_input = QLineEdit(self)
        self.price_6m_input.setPlaceholderText("6개월 전 가격")
        self.current_price_input = QLineEdit(self)
        self.current_price_input.setPlaceholderText("현재 가격")

        input_layout.addWidget(self.ticker_input)
        input_layout.addWidget(self.name_input)
        input_layout.addWidget(self.price_1y_input)
        input_layout.addWidget(self.price_6m_input)
        input_layout.addWidget(self.current_price_input)

        # 상단 버튼 레이아웃
        button_layout = QHBoxLayout()

        self.add_button = QPushButton("추가")
        self.update_button = QPushButton("수정")
        self.delete_button = QPushButton("삭제")
        self.reset_button = QPushButton("초기화")

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.reset_button)

        layout.addLayout(input_layout)
        layout.addLayout(button_layout)

        # 주식 테이블 설정
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(5)
        self.stock_table.setHorizontalHeaderLabels(
            ["틱커명", "종목명", "1년전가격", "6개월전가격", "현재가격"])
        self.stock_table.horizontalHeader().setSectionResizeMode(
            0, self.stock_table.horizontalHeader().Stretch)
        self.stock_table.horizontalHeader().setSectionResizeMode(
            1, self.stock_table.horizontalHeader().Stretch)
        self.stock_table.horizontalHeader().setSectionResizeMode(
            2, self.stock_table.horizontalHeader().Stretch)
        self.stock_table.horizontalHeader().setSectionResizeMode(
            3, self.stock_table.horizontalHeader().Stretch)
        self.stock_table.horizontalHeader().setSectionResizeMode(
            4, self.stock_table.horizontalHeader().Stretch)

        layout.addWidget(self.stock_table)

        # 인용구 박스 추가
        quote_box = QLabel("made by 나종춘(2024)")
        quote_box.setObjectName("quoteBox")  # QSS에서 스타일 적용을 위해 ObjectName 설정
        quote_box.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        quote_box.setFixedSize(800, 20)
        layout.addWidget(quote_box)

        # 초기 데이터 테이블에 로드
        self.update_table(self.stock_data)

        # 이벤트 연결
        self.reset_button.clicked.connect(self.clear_input_fields)  # 초기화 버튼
        self.add_button.clicked.connect(self.add_stock)
        self.update_button.clicked.connect(self.update_stock)
        self.delete_button.clicked.connect(self.delete_stock)
        self.stock_table.cellClicked.connect(self.load_stock_data)

        self.ticker_input.textChanged.connect(self.auto_fill_fields)

    def center_window(self):
        """창을 화면 중앙에 배치합니다."""
        screen = QScreen.availableGeometry(QApplication.primaryScreen())
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2,
                  (screen.height() - size.height()) // 2)

    def convert_to_uppercase(self):
        """틱커명을 대문자로 변환합니다."""
        self.ticker_input.setText(self.ticker_input.text().upper())

    def load_data(self):
        """JSON 파일에서 데이터를 로드합니다."""
        try:
            with open(self.data_file, "r", encoding="utf-8") as file:
                self.stock_data = json.load(file)
        except FileNotFoundError:
            self.stock_data = []

    def save_data(self):
        """데이터를 JSON 파일에 저장합니다."""
        with open(self.data_file, "w", encoding="utf-8") as file:
            json.dump(self.stock_data, file, ensure_ascii=False, indent=4)

    def update_table(self, stock_data):
        """테이블을 주식 데이터로 업데이트합니다."""
        self.stock_table.setRowCount(len(stock_data))
        for row_idx, row_data in enumerate(stock_data):
            for col_idx, value in enumerate(row_data.values()):
                item = QTableWidgetItem(str(value))
                if col_idx in [0, 1]:  # 틱커명과 종목명은 왼쪽 정렬
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                else:  # 가격 정보는 오른쪽 정렬
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.stock_table.setItem(row_idx, col_idx, item)

    def add_stock(self):
        """입력된 데이터를 테이블과 JSON에 추가합니다."""
        ticker = self.ticker_input.text()
        name = self.name_input.text()
        price_1y = int(self.price_1y_input.text()
                       ) if self.price_1y_input.text() else 0
        price_6m = int(self.price_6m_input.text()
                       ) if self.price_6m_input.text() else 0
        current_price = int(self.current_price_input.text()
                            ) if self.current_price_input.text() else 0

        stock_entry = {
            "틱커명": ticker,
            "종목명": name,
            "1년 전 가격": price_1y,
            "6개월 전 가격": price_6m,
            "현재 가격": current_price
        }

        self.stock_data.append(stock_entry)
        self.update_table(self.stock_data)
        self.save_data()  # 데이터를 JSON 파일에 저장

        self.clear_input_fields()

    def update_stock(self):
        """입력된 데이터를 선택된 행에 업데이트하고 JSON에 반영합니다."""
        selected_row = self.stock_table.currentRow()
        if selected_row >= 0:
            self.stock_data[selected_row] = {
                "틱커명": self.ticker_input.text(),
                "종목명": self.name_input.text(),
                "1년 전 가격": int(self.price_1y_input.text()) if self.price_1y_input.text() else 0,
                "6개월 전 가격": int(self.price_6m_input.text()) if self.price_6m_input.text() else 0,
                "현재 가격": int(self.current_price_input.text()) if self.current_price_input.text() else 0
            }
            self.update_table(self.stock_data)
            self.save_data()  # 데이터를 JSON 파일에 저장

    def delete_stock(self):
        """선택된 행을 테이블과 JSON에서 삭제합니다."""
        selected_row = self.stock_table.currentRow()
        if selected_row >= 0:  # 유효한 선택인지 확인
            del self.stock_data[selected_row]
            self.update_table(self.stock_data)
            self.save_data()  # 데이터를 JSON 파일에 저장

    def load_stock_data(self, row, column):
        """선택된 행의 데이터를 입력 필드로 불러옵니다."""
        stock_entry = self.stock_data[row]
        self.ticker_input.setText(stock_entry["틱커명"])
        self.name_input.setText(stock_entry["종목명"])
        self.price_1y_input.setText(str(stock_entry["1년 전 가격"]))
        self.price_6m_input.setText(str(stock_entry["6개월 전 가격"]))
        self.current_price_input.setText(str(stock_entry["현재 가격"]))

    def auto_fill_fields(self):
        """틱커명을 입력하면 관련된 필드를 자동으로 채웁니다."""
        ticker = self.ticker_input.text().upper()
        if ticker:
            stock = yf.Ticker(ticker)
            self.name_input.setText(stock.info.get('shortName', 'N/A'))
            hist = stock.history(period="1y")
            if not hist.empty:
                self.price_1y_input.setText(
                    str(int(hist['Close'].iloc[0]) if not np.isnan(hist['Close'].iloc[0]) else 0))
                self.price_6m_input.setText(str(
                    int(hist['Close'].iloc[-126]) if not np.isnan(hist['Close'].iloc[-126]) else 0))
                self.current_price_input.setText(
                    str(int(hist['Close'].iloc[-1]) if not np.isnan(hist['Close'].iloc[-1]) else 0))
            else:
                self.price_1y_input.clear()
                self.price_6m_input.clear()
                self.current_price_input.clear()
        else:
            self.clear_input_fields()

    def clear_input_fields(self):
        """입력 필드를 초기화합니다."""
        self.ticker_input.clear()
        self.name_input.clear()
        self.price_1y_input.clear()
        self.price_6m_input.clear()
        self.current_price_input.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 스타일 시트 적용 (UTF-8로 인코딩 설정)
    with open("css.qss", "r", encoding="utf-8") as style_file:
        app.setStyleSheet(style_file.read())

    window = StockApp()
    window.show()
    sys.exit(app.exec_())
