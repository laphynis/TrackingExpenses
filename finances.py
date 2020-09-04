import csv
import kivy
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from kivy.uix.screenmanager import ScreenManager, Screen
import datetime
from datetime import date, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns



class ScreenManagement(ScreenManager):
    def __init__(self, **kwargs):
        super(ScreenManagement, self).__init__(**kwargs)

        #creating a screen for each page
        self.welcome = Screen(name='welcome_page')
        self.home = Screen(name='home_page')

        #adding widget to the screen manager
        self.add_widget(self.welcome)
        self.add_widget(self.home)

        #working with welcome UI 
        welcomeUI = WelcomeUI()
        welcomeUI.go.bind(on_press=self.move_home)
        self.welcome.add_widget(welcomeUI)

        #working with home page UI
        homeUI = HomePage()
        self.home.add_widget(homeUI)
        
    def move_home(self, *args):
        self.current = 'home_page'



class WelcomeUI(GridLayout):
    def __init__(self, **kwargs):
        super(WelcomeUI, self).__init__(**kwargs)
        self.cols = 1
        
        self.welcome = AnchorLayout(anchor_x='center',
                                    anchor_y='top')
        self.welcome.add_widget(Label(text='Welcome back!',
                              font_size = 40))
        
        current_time = datetime.datetime.today()
        current_time = current_time.strftime('\n%B %d, %Y \n%H:%M:%S')

        self.time = AnchorLayout(anchor_x='center',
                                 anchor_y='center')
        self.time.add_widget(Label(text='Today\'s date and time is: {}'.format(
            current_time)))

        self.press = AnchorLayout(anchor_x='center',
                                  anchor_y='bottom')
        self.go = Button(text='Continue',
                         size_hint = (0.2, 0.2))
        self.press.add_widget(self.go)

        self.add_widget(self.welcome)
        self.add_widget(self.time)
        self.add_widget(self.press)
    
        
class HomePage(FloatLayout):
    def __init__(self, **kwargs):
        super(HomePage, self).__init__(**kwargs)

        #getting the dates
        self.today_date = datetime.datetime.today()
        self.date = self.today_date.strftime('%Y-%m-%d')

        #creating a dataframe and initializing lists/dictionaries
        self.dataframe = pd.read_csv('spending.csv')
        self.list_of_days = []
        self.price_dict = {}
        self.cat_dict = {}

        #creating iterables to get the relevant information
        self.thirty_days_ago = pd.date_range(self.today_date - timedelta(days=30),
                                        self.today_date, freq='d')
        self.thirty_days_ago = self.thirty_days_ago.date

        self.list_of_types = ['Food', 'Gas', 'School', 'Entertainment',
                         'Utilities', 'Groceries', 'Other']

        #formatting everything properly
        for date in self.thirty_days_ago:
            date = date.strftime('%Y-%m-%d')
            self.list_of_days.append(date)

        for date in self.list_of_days:
            self.price_dict[date] = 0

        for types in self.list_of_types:
            self.cat_dict[types] = 0

        #filter dataframe by the last 30 days and apply a function to get the $$ spent
        self.filtered_df = self.dataframe.loc[self.dataframe['Date'].isin(self.list_of_days)]
        self.filtered_df.apply(lambda row: self.matching_dates(row['Date'], row['Spent'],
                                                               self.price_dict), axis=1)

        #filter dataframe by type and add a count for each one from the last 30 days
        self.no_none_df = self.filtered_df.loc[self.dataframe['Type'].isin(self.list_of_types)]
        self.no_none_df.apply(lambda row: self.matching_dates(row['Type'], row['Spent'],
                                                              self.cat_dict), axis=1)

        #making a new dataframe of the information using dictionaries
        self.prices_from_30_days = pd.DataFrame(self.price_dict.items(),
                                                columns=['Date', 'Spent'])
        self.count_from_30_days = pd.DataFrame(self.cat_dict.items(),
                                                columns=['Type', 'Spent'])

        self.sum = self.prices_from_30_days['Spent'].sum()

        #creating a layout for the plot
        self.plot_layout = AnchorLayout(anchor_x='center', anchor_y='center')
        
        self.graph = self.plot_graph(self.prices_from_30_days, 'Date', 'Spent', 'line')

        self.add_widget(self.plot_layout)

        self.total_label = Label(text='Total Amount Spent Over 30 Days: ' +
                                 f'${self.sum}',
                                 pos_hint={'x':-0.3,'y':.45})
        self.add_widget(self.total_label)            
        
        self.date_button = Button(text='By Date', size_hint=(.2, .05),
                                  pos_hint={'x':0, 'y':.825})
        self.date_button.bind(on_press=lambda *args: self.plot_graph(self.prices_from_30_days,
                                                                     'Date', 'Spent', 'line',
                                                                     *args))
        self.add_widget(self.date_button)

        self.type_button = Button(text='By Type', size_hint=(.2, .05),
                                  pos_hint={'x':.2, 'y':.825})
        self.type_button.bind(on_press=lambda *args: self.plot_graph(self.count_from_30_days,
                                                                     'Type', 'Spent', 'bar',
                                                                     *args))
        self.add_widget(self.type_button)
                
        #creating a button that allows users to enter new data
        self.enter_new_entry = Button(text='Enter a new entry',
                                      size_hint=(.5, .15),
                                      pos_hint={'x': .25, 'y':0})
        self.enter_new_entry.bind(on_press=self.open_popup)
        self.add_widget(self.enter_new_entry)

        #creating a popup for when enter_new_entry is pressed
        self.popup_box = FloatLayout()
        self.popup_submit = Button(text='Submit',
                                   size_hint=(.45, .2),
                                   pos_hint={'x':.05, 'y':.05})
        self.popup_submit.bind(on_press=self.submit)
        self.popup_box.add_widget(self.popup_submit)
        
        self.popup_cancel = Button(text='Cancel',
                                   size_hint=(.45, .2),
                                   pos_hint={'x':.5, 'y':.05})
        self.popup_cancel.bind(on_press=self.close_popup)
        self.popup_box.add_widget(self.popup_cancel)

        #creating a list of options for the pop up
        self.food = Button(text='Food',
                           size_hint=(.25,.1),
                           pos_hint={'x':0, 'y':.8})
        self.food.bind(on_press=lambda *args: self.update_choice(self.food, *args))

        self.gas = Button(text='Gas',
                           size_hint=(.25,.1),
                           pos_hint={'x':.25, 'y':.8})
        self.gas.bind(on_press=lambda *args: self.update_choice(self.gas, *args))

        self.grocery = Button(text='Groceries',
                           size_hint=(.25,.1),
                           pos_hint={'x':.5, 'y':.8})
        self.grocery.bind(on_press=lambda *args: self.update_choice(self.grocery, *args))

        self.entertain = Button(text='Entertainment',
                           size_hint=(.25,.1),
                           pos_hint={'x':.75, 'y':.8})
        self.entertain.bind(on_press=lambda *args: self.update_choice(self.entertain, *args))

        self.utility = Button(text='Utilities',
                           size_hint=(.25,.1),
                           pos_hint={'x':.125, 'y':.7})
        self.utility.bind(on_press=lambda *args: self.update_choice(self.utility, *args))

        self.school = Button(text='School',
                           size_hint=(.25,.1),
                           pos_hint={'x':.375, 'y':.7})
        self.school.bind(on_press=lambda *args: self.update_choice(self.school, *args))

        self.other = Button(text='Other',
                           size_hint=(.25,.1),
                           pos_hint={'x':.625, 'y':.7})
        self.other.bind(on_press=lambda *args: self.update_choice(self.other, *args))

        self.popup_box.add_widget(self.food)
        self.popup_box.add_widget(self.gas)
        self.popup_box.add_widget(self.grocery)
        self.popup_box.add_widget(self.entertain)
        self.popup_box.add_widget(self.utility)
        self.popup_box.add_widget(self.school)
        self.popup_box.add_widget(self.other)
        
        self.category = Label(text='Category: ',
                          pos_hint={'x':-.2, 'y':.1})
        self.popup_box.add_widget(self.category)
        
        self.choice_label = Label(text='',
                                  pos_hint={'x':.05, 'y':.1})
        self.popup_box.add_widget(self.choice_label)

        #text input box for users to put in the amount of money they spent
        self.spending = Label(text='$$ Spent: ',
                              pos_hint={'x':-.2, 'y':-.05})
        self.popup_box.add_widget(self.spending)

        
        self.text_box = TextInput(text='',
                                  size_hint=(0.35, 0.12),
                                  pos_hint={'x':.45,'y':.39})
        self.popup_box.add_widget(self.text_box)
        
        self.popup = Popup(title='Enter the following',
                           content=self.popup_box,
                           size_hint=(.5, .5),
                           auto_dismiss=False)

        
    #opens the popup upon press
    def open_popup(self, *args):
        self.popup.open()

    def close_popup(self, *args):
        #resetting the popup box after cancelling
        self.popup.dismiss()
        self.choice_label.text = ''
        self.text_box.text = ''

    #function that updates the information from the existing dataframes and dictionaries
    def submit(self, *args):
        money_spent = self.text_box.text
        category_spend = self.choice_label.text
        self.price_dict[self.date] = self.price_dict[self.date] + float(money_spent)
        self.prices_from_30_days = pd.DataFrame(self.price_dict.items(),
                                                columns=['Date', 'Spent'])

        self.cat_dict[category_spend] = self.cat_dict[category_spend] + float(money_spent)
        self.count_from_30_days = pd.DataFrame(self.cat_dict.items(),
                                                columns=['Type', 'Spent'])
        
        self.sum = self.prices_from_30_days['Spent'].sum()
        self.total_label.text = f'Total Amount Spent Over 30 Days: ${self.sum}'

        self.graph = self.plot_graph(self.prices_from_30_days, 'Date', 'Spent', 'line')
        
        #writing into the csv file
        with open('spending.csv', 'a+', newline='') as self.data_file:
            self.writer = csv.writer(self.data_file)
            self.writer.writerow([self.date,category_spend, money_spent])
            self.data_file.close()
        
        #resetting the pop up box after submitting
        self.popup.dismiss()
        self.choice_label.text = ''
        self.text_box.text = ''

    def update_choice(self, button, *args):
        self.choice_label.text = button.text

    def plot_graph(self, df, x_val, y_val, graph_type,*args):
        df.plot(x=x_val, y=y_val, kind=graph_type)
        if x_val == 'Type':
            plt.xticks(rotation=360)
        plt.title('Spending Over the Last 30 Days')
        self.plot_layout.add_widget(FigureCanvasKivyAgg(plt.gcf(),
                                                       size_hint=(1, 0.65)))
        
    #function that is used to iterate through rows of dataframe and update $$ spent
    def matching_dates(self, val, price, dictionary, *args):
        if val in dictionary:
            dictionary[val] = dictionary[val] + price
        else:
            pass
        
                                      
class myApp(App):
    def build(self):
        #getting today's date
        self.today_date = datetime.datetime.today()
        self.date = self.today_date.strftime('%Y-%m-%d')

        #creating a dataframe of the existing information
        self.dataframe = pd.read_csv('spending.csv')

        #gettings the dates of the last 30 days
        thirty_days_ago = pd.date_range(self.today_date - timedelta(days=30),
                                        self.today_date, freq='d')
        thirty_days_ago = thirty_days_ago.date

        #checking if any of the last 30 days are missing in the dataframe
        for date in thirty_days_ago:
            date = date.strftime('%Y-%m-%d')
            #if any are missing, update csv
            if date not in self.dataframe.values:
                with open('spending.csv', 'a+', newline='') as self.data_file:
                    self.writer = csv.writer(self.data_file)
                    self.writer.writerow([date,'None', 0])
                    self.data_file.close()

            else:
                pass
        
        return ScreenManagement()

if __name__ == '__main__':
    myApp().run()


