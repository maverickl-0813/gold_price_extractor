import yaml
from datetime import datetime
import requests
from io import StringIO
import pandas as pd
import plotly.graph_objects as go


class GoldPriceExtractor:

    def __init__(self):
        with open("properties.yaml", 'r', encoding="utf-8") as fstream:
            data = yaml.safe_load(fstream)
        self.url = data.get("bot_url")
        self.gold_price_csv = data.get("gold_price_history_path")
        self.elements = data.get("bot_elements")
        self.prices = {'current_buy_price': 0, 'current_sell_price': 0}
        self.price_table = pd.DataFrame(columns=["Date", "Buy Price", "Sell Price"])
        self.today = datetime.today()

    def _get_current_gold_price(self):
        web_content = requests.get(self.url)
        if web_content.ok:
            df_list = pd.read_html(StringIO(web_content.text), header=0)
            df = df_list[0]
            self.prices['current_buy_price'] = int(df.iloc[1].iloc[2].split()[0])
            self.prices['current_sell_price'] = int(df.iloc[2].iloc[2].split()[0])
            return True
        else:
            print("Can't get current prices for now.")
            return False

    def _load_price_history(self):
        try:
            self.price_table = pd.read_csv(self.gold_price_csv)
        except FileNotFoundError:
            raise

    def _update_price_history(self):
        date_format = "%Y-%m-%d"
        latest_csv_day = self.price_table[["Date"]].tail(1).values[0][0]
        latest_csv_day_obj = datetime.strptime(latest_csv_day, date_format)
        if self.today == latest_csv_day_obj:
            print("No need to update, already have the latest price.")
        elif self._get_current_gold_price():
            self.price_table.loc[len(self.price_table.index)] = [self.today.strftime(date_format),
                                                                 self.prices.get("current_buy_price"),
                                                                 self.prices.get("current_sell_price")]
            self.price_table.to_csv(self.gold_price_csv)

    def get_buy_price(self):
        if not self.prices['current_buy_price']:
            self._get_current_gold_price()
        return self.prices.get("current_buy_price")

    def get_sell_price(self):
        if not self.prices['current_sell_price']:
            self._get_current_gold_price()
        return self.prices.get("current_sell_price")

    def _draw_figure(self, title, **kwargs):
        fig = go.Figure()
        indices = list(range(0, len(self.price_table), len(self.price_table) // 2))
        fig.add_trace(go.Scatter(x=self.price_table['Date'], y=self.price_table['Buy Price'], mode='lines+markers',
                                 name=kwargs.get("buy_title")))
        fig.add_trace(go.Scatter(x=self.price_table['Date'][indices], y=self.price_table['Buy Price'][indices],
                                 mode='markers+text',
                                 marker=dict(size=10), showlegend=False,
                                 text=self.price_table['Buy Price'][indices],
                                 textposition="top center",
                                 hovertemplate=kwargs.get("buy_hover_template")))
        fig.add_trace(go.Scatter(x=self.price_table['Date'], y=self.price_table['Sell Price'], mode='lines+markers',
                                 name=kwargs.get("sell_title")))
        fig.add_trace(go.Scatter(x=self.price_table['Date'][indices], y=self.price_table['Sell Price'][indices],
                                 mode='markers+text',
                                 marker=dict(size=10), showlegend=False,
                                 text=self.price_table['Sell Price'][indices],
                                 textposition="top center",
                                 hovertemplate=kwargs.get("sell_hover_template")))
        fig.update_layout(title=title, xaxis_title="日期", yaxis_title="價格 (新台幣)")
        fig.show()

    def show_price_figure(self):
        if len(self.price_table.index) == 0:
            try:
                self._load_price_history()
            except FileNotFoundError:
                print("Price history is not loaded properly. Cannot Proceed.")
                return

        if self.today.isoweekday() in [6, 7]:
            print("It's weekend, no need to update price from web.")
        else:
            self._update_price_history()

        fig_title = "台灣銀行黃金牌價"
        buy_title = "賣出價格"
        buy_hover_template = buy_title + ": %{text} <extra></extra>"
        sell_title = "買進價格"
        sell_hover_template = sell_title + ": %{text} <extra></extra>"

        self._draw_figure(title=fig_title,
                          buy_title=buy_title, buy_hover_template=buy_hover_template,
                          sell_title=sell_title, sell_hover_template=sell_hover_template)


if __name__ == '__main__':
    price_extractor = GoldPriceExtractor()
    price_extractor.show_price_figure()
