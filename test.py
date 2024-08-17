import configparser  # configparser 모듈 임포트
import sys
import os
import json
import yfinance as yf
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QTableWidget, QTableWidgetItem, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QScreen

# 현재 스크립트의 경로를 기준으로 파일 경로 설정
script_dir = os.path.dirname(os.path.abspath(__file__))

# config.ini 파일 경로 설정
config_path = os.path.join(script_dir, 'config.ini')

# ConfigParser 초기화 및 파일 읽기 (UTF-8로 인코딩하여 파일 읽기)
config = configparser.ConfigParser()
with open(config_path, 'r', encoding='utf-8') as config_file:
    config.read_file(config_file)


class StockApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(config.get('General', 'app_name'))
        self.setGeometry(100, 100, config.getint(
            'Window', 'width'), config.getint('Window', 'height'))
        self.center_window()

        # config 파일에 정의된 경로를 사용하여 파일 경로 설정
        self.data_file = os.path.join(
            script_dir, config.get('Paths', 'data_file'))
        self.css_file = os.path.join(
            script_dir, config.get('Paths', 'css_file'))

        # 데이터 저장 및 로드
        self.load_data()

        # UI 구성
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        title_label = QLabel("Current Stock Status")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        input_layout = QHBoxLayout()

        self.ticker_input = QLineEdit(self)
        self.ticker_input.setPlaceholderText("틱커명")
        self.ticker_input.textChanged.connect(self.convert_to_uppercase)
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

        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(5)
        self.stock_table.setHorizontalHeaderLabels(
            ["틱커명", "종목명", "1년 전 가격", "6개월 전 가격", "현재 가격"])
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
        quote_box = QLabel("made by 나종춘(2024)")
        quote_box.setObjectName("quoteBox")
        quote_box.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        quote_box.setFixedSize(800, 20)
        layout.addWidget(quote_box)

        self.update_table(self.stock_data)
        self.reset_button.clicked.connect(self.clear_input_fields)
        self.add_button.clicked.connect(self.add_stock)
        self.update_button.clicked.connect(self.update_stock)
        self.delete_button.clicked.connect(self.delete_stock)
        self.stock_table.cellClicked.connect(self.load_stock_data)

        # 스타일 시트 적용
        if config.getboolean('UI', 'use_stylesheet'):
            self.apply_stylesheet()

    def center_window(self):
        if config.getboolean('Window', 'center_window'):
            screen = QScreen.availableGeometry(QApplication.primaryScreen())
            size = self.geometry()
            self.move((screen.width() - size.width()) // 2,
                      (screen.height() - size.height()) // 2)

    def load_data(self):
        try:
            with open(self.data_file, "r", encoding="utf-8") as file:
                self.stock_data = json.load(file)
        except FileNotFoundError:
            self.stock_data = []

    def save_data(self):
        with open(self.data_file, "w", encoding="utf-8") as file:
            json.dump(self.stock_data, file, ensure_ascii=False, indent=4)

    def update_table(self, stock_data):
        self.stock_table.setRowCount(len(stock_data))
        for row_idx, row_data in enumerate(stock_data):
            for col_idx, value in enumerate(row_data.values()):
                item = QTableWidgetItem(str(value))
                if col_idx in [0, 1]:
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.stock_table.setItem(row_idx, col_idx, item)

    def add_stock(self):
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
        self.save_data()
        self.clear_input_fields()

    def update_stock(self):
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
            self.save_data()

    def delete_stock(self):
        selected_row = self.stock_table.currentRow()
        if selected_row >= 0:
            del self.stock_data[selected_row]
            self.update_table(self.stock_data)
            self.save_data()

    def load_stock_data(self, row, column):
        stock_entry = self.stock_data[row]
        self.ticker_input.setText(stock_entry["틱커명"])
        self.name_input.setText(stock_entry["종목명"])
        self.price_1y_input.setText(str(stock_entry["1년 전 가격"]))
        self.price_6m_input.setText(str(stock_entry["6개월 전 가격"]))
        self.current_price_input.setText(str(stock_entry["현재 가격"]))

    def convert_to_uppercase(self):
        self.ticker_input.setText(self.ticker_input.text().upper())

    def apply_stylesheet(self):
        try:
            with open(self.css_file, "r", encoding="utf-8") as style_file:
                self.setStyleSheet(style_file.read())
        except FileNotFoundError:
            print("CSS 파일을 찾을 수 없습니다. 기본 스타일을 사용합니다.")

    def clear_input_fields(self):
        self.ticker_input.clear()
        self.name_input.clear()
        self.price_1y_input.clear()
        self.price_6m_input.clear()
        self.current_price_input.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StockApp()
    window.show()
    sys.exit(app.exec_())
