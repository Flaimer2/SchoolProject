import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)
from datetime import datetime, timedelta

from matplotlib.ticker import MaxNLocator


class BusScheduleOptimizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Оптимизатор расписания автобусов")
        self.root.geometry("1000x700")

        self.routes = []
        self.schedules = {}
        self.editing_index = None
        self.stops = []
        self.stop_routes = {}
        self.route_stops = {}

        self.create_widgets()

    def create_widgets(self):
        tab_control = ttk.Notebook(self.root)
        self.tab1 = ttk.Frame(tab_control)
        self.tab2 = ttk.Frame(tab_control)
        self.tab3 = ttk.Frame(tab_control)
        self.tab4 = ttk.Frame(tab_control)
        self.tab5 = ttk.Frame(tab_control)
        tab_control.add(self.tab1, text='Добавление маршрутов')
        tab_control.add(self.tab2, text='Оптимизация расписания')
        tab_control.add(self.tab3, text='Визуализация')
        tab_control.add(self.tab4, text='Управление остановками')
        tab_control.add(self.tab5, text='Расписание по остановкам')
        tab_control.pack(expand=1, fill="both")

        self.setup_route_tab()
        self.setup_optimization_tab()
        self.setup_visualization_tab()
        self.setup_stops_tab()
        self.setup_schedule_by_stop_tab()

    def setup_route_tab(self):
        frame = ttk.LabelFrame(self.tab1, text="Информация о маршруте")
        frame.grid(column=0, row=0, padx=10, pady=10, sticky="NSEW")

        ttk.Label(frame, text="Номер маршрута:").grid(column=0, row=0, sticky="W", padx=5, pady=5)
        self.route_number = ttk.Entry(frame, width=10)
        self.route_number.grid(column=1, row=0, sticky="W", padx=5, pady=5)

        ttk.Label(frame, text="Начальная остановка:").grid(column=0, row=1, sticky="W", padx=5, pady=5)
        self.start_stop = ttk.Combobox(frame, width=30)
        self.start_stop.grid(column=1, row=1, sticky="W", padx=5, pady=5)

        ttk.Label(frame, text="Конечная остановка:").grid(column=0, row=2, sticky="W", padx=5, pady=5)
        self.end_stop = ttk.Combobox(frame, width=30)
        self.end_stop.grid(column=1, row=2, sticky="W", padx=5, pady=5)

        ttk.Label(frame, text="Промежуточные остановки:").grid(column=0, row=3, sticky="W", padx=5, pady=5)

        stops_frame = ttk.Frame(frame)
        stops_frame.grid(column=1, row=3, sticky="W", padx=5, pady=5)

        self.stops_listbox = tk.Listbox(stops_frame, selectmode=tk.MULTIPLE, width=30, height=5)
        self.stops_listbox.pack(side=tk.LEFT, fill=tk.BOTH)

        scrollbar = ttk.Scrollbar(stops_frame, orient="vertical", command=self.stops_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.stops_listbox.configure(yscrollcommand=scrollbar.set)

        stops_buttons_frame = ttk.Frame(frame)
        stops_buttons_frame.grid(column=1, row=4, sticky="W", padx=5, pady=5)

        ttk.Label(frame, text="Примерное время в пути (мин):").grid(column=0, row=5, sticky="W", padx=5, pady=5)
        self.travel_time = ttk.Entry(frame, width=10)
        self.travel_time.grid(column=1, row=5, sticky="W", padx=5, pady=5)

        ttk.Label(frame, text="Загруженность (1-10):").grid(column=0, row=6, sticky="W", padx=5, pady=5)
        self.busyness = ttk.Scale(frame, from_=1, to=10, orient="horizontal")
        self.busyness.grid(column=1, row=6, sticky="W", padx=5, pady=5)

        buttons_frame = ttk.Frame(frame)
        buttons_frame.grid(column=0, row=7, columnspan=2, pady=10)

        self.add_button = ttk.Button(buttons_frame, text="Добавить маршрут", command=self.add_route)
        self.add_button.grid(column=0, row=0, padx=5)

        ttk.Button(buttons_frame, text="Загрузить примеры", command=self.load_example).grid(column=1, row=0, padx=5)

        self.setup_routes_table()

        self.setup_optimization_tab()

    def configure_stop_times(self, stop_name):
        time_window = tk.Toplevel(self.root)
        time_window.title(f"Время прибытия для {stop_name}")

        times = {}
        for route_num in self.stop_routes[stop_name]:
            frame = ttk.Frame(time_window)
            frame.pack(padx=10, pady=5, fill='x')

            ttk.Label(frame, text=f"Маршрут {route_num}:").pack(side='left')
            time_var = tk.StringVar(value=str(self.route_stops.get(route_num, {}).get(stop_name, 0)))
            times[route_num] = time_var

            entry = ttk.Entry(frame, textvariable=time_var, width=5)
            entry.pack(side='right')
            ttk.Label(frame, text="мин").pack(side='right')

        def save_times():
            for route_num, var in times.items():
                try:
                    time = int(var.get())
                    if route_num not in self.route_stops:
                        self.route_stops[route_num] = {}
                    self.route_stops[route_num][stop_name] = time
                except ValueError:
                    messagebox.showerror("Ошибка", "Введите целое число минут")
                    return
            time_window.destroy()

        ttk.Button(time_window, text="Сохранить", command=save_times).pack(pady=10)

    def setup_routes_table(self):
        frame = ttk.LabelFrame(self.tab1, text="Добавленные маршруты")
        frame.grid(column=0, row=2, padx=10, pady=10, sticky="NSEW")

        columns = ('route_num', 'start', 'end', 'stops', 'time', 'busyness')
        self.routes_table = ttk.Treeview(frame, columns=columns, show='headings')

        self.routes_table.heading('route_num', text='№')
        self.routes_table.heading('start', text='Начало')
        self.routes_table.heading('end', text='Конец')
        self.routes_table.heading('stops', text='Кол-во остановок')
        self.routes_table.heading('time', text='Время (мин)')
        self.routes_table.heading('busyness', text='Загруженность')

        self.routes_table.column('route_num', width=50)
        self.routes_table.column('start', width=120)
        self.routes_table.column('end', width=120)
        self.routes_table.column('stops', width=100)
        self.routes_table.column('time', width=80)
        self.routes_table.column('busyness', width=100)

        self.routes_table.grid(column=0, row=0, sticky="NSEW")

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.routes_table.yview)
        self.routes_table.configure(yscroll=scrollbar.set)
        scrollbar.grid(column=1, row=0, sticky='NS')

        button_frame = ttk.Frame(frame)
        button_frame.grid(column=0, row=1, pady=5)

        ttk.Button(button_frame, text="Удалить выбранный", command=self.delete_route).grid(column=0, row=0, padx=5)
        ttk.Button(button_frame, text="Редактировать выбранный", command=self.edit_route).grid(column=1, row=0, padx=5)

        self.routes_table.bind("<Double-1>", lambda event: self.edit_route())

    def setup_optimization_tab(self):
        frame = ttk.LabelFrame(self.tab2, text="Параметры оптимизации")
        frame.grid(column=0, row=0, padx=10, pady=10, sticky="NSEW")

        ttk.Label(frame, text="Начало рабочего дня (часы):").grid(column=0, row=0, sticky="W", padx=5, pady=5)
        self.start_hour = ttk.Spinbox(frame, from_=4, to=10, width=5)
        self.start_hour.set(6)
        self.start_hour.grid(column=1, row=0, sticky="W", padx=5, pady=5)

        ttk.Label(frame, text="Конец рабочего дня (часы):").grid(column=0, row=1, sticky="W", padx=5, pady=5)
        self.end_hour = ttk.Spinbox(frame, from_=18, to=23, width=5)
        self.end_hour.set(22)
        self.end_hour.grid(column=1, row=1, sticky="W", padx=5, pady=5)

        ttk.Label(frame, text="Утренний час пик:").grid(column=0, row=2, sticky="W", padx=5, pady=5)
        self.morning_peak = ttk.Checkbutton(frame, text="7:00 - 9:00")
        self.morning_peak.state(['!alternate', 'selected'])
        self.morning_peak.grid(column=1, row=2, sticky="W", padx=5, pady=5)

        ttk.Label(frame, text="Вечерний час пик:").grid(column=0, row=3, sticky="W", padx=5, pady=5)
        self.evening_peak = ttk.Checkbutton(frame, text="17:00 - 19:00")
        self.evening_peak.state(['!alternate', 'selected'])
        self.evening_peak.grid(column=1, row=3, sticky="W", padx=5, pady=5)

        ttk.Label(frame, text="Количество автобусов:").grid(column=0, row=4, sticky="W", padx=5, pady=5)
        self.buses_count = ttk.Spinbox(frame, from_=1, to=20, width=5)
        self.buses_count.set(5)
        self.buses_count.grid(column=1, row=4, sticky="W", padx=5, pady=5)

        ttk.Label(frame, text="Минимальный интервал между автобусами (мин):").grid(column=0, row=5, sticky="W", padx=5,
                                                                                   pady=5)
        self.min_interval = ttk.Spinbox(frame, from_=1, to=30, width=5)
        self.min_interval.set(10)
        self.min_interval.grid(column=1, row=5, sticky="W", padx=5, pady=5)

        optimize_button_frame = ttk.Frame(frame)
        optimize_button_frame.grid(column=0, row=6, columnspan=2, pady=10)

        ttk.Button(optimize_button_frame, text="Оптимизировать расписание", command=self.optimize_schedule).grid(
            column=0, row=0, padx=5)

        result_frame = ttk.LabelFrame(self.tab2, text="Результаты оптимизации")
        result_frame.grid(column=0, row=1, padx=10, pady=10, sticky="NSEW")

        self.optimization_result = scrolledtext.ScrolledText(result_frame, width=80, height=20)
        self.optimization_result.grid(column=0, row=0, sticky="NSEW", padx=5, pady=5)

        self.tab2.columnconfigure(0, weight=1)
        self.tab2.rowconfigure(1, weight=1)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)

    def setup_visualization_tab(self):
        frame = ttk.LabelFrame(self.tab3, text="Визуализация расписания")
        frame.grid(column=0, row=0, padx=10, pady=10, sticky="NSEW")

        ttk.Label(frame, text="Выберите маршрут:").grid(column=0, row=0, sticky="W", padx=5, pady=5)
        self.route_for_viz = ttk.Combobox(frame, width=10)
        self.route_for_viz.grid(column=1, row=0, sticky="W", padx=5, pady=5)

        ttk.Button(frame, text="Построить график", command=self.visualize_schedule).grid(column=2, row=0, padx=5,
                                                                                         pady=5)

        self.chart_frame = ttk.Frame(self.tab3)
        self.chart_frame.grid(column=0, row=1, padx=10, pady=10, sticky="NSEW")
        self.tab3.columnconfigure(0, weight=1)
        self.tab3.rowconfigure(1, weight=1)

    def setup_stops_tab(self):
        frame = ttk.LabelFrame(self.tab4, text="Управление остановками")
        frame.grid(column=0, row=0, padx=10, pady=10, sticky="NSEW")

        ttk.Label(frame, text="Название остановки:").grid(column=0, row=0, sticky="W", padx=5, pady=5)
        self.stop_name_entry = ttk.Entry(frame, width=30)
        self.stop_name_entry.grid(column=1, row=0, sticky="W", padx=5, pady=5)

        button_frame = ttk.Frame(frame)
        button_frame.grid(column=0, row=1, columnspan=2, padx=5, pady=5)

        ttk.Button(button_frame, text="Добавить остановку", command=self.add_stop).grid(column=0, row=0, padx=5, pady=5)
        ttk.Button(button_frame, text="Удалить остановку", command=self.delete_stop).grid(column=1, row=0, padx=5,
                                                                                          pady=5)

        stops_frame = ttk.LabelFrame(self.tab4, text="Список остановок")
        stops_frame.grid(column=0, row=1, padx=10, pady=10, sticky="NSEW")

        columns = ('stop_name', 'routes')
        self.stops_table = ttk.Treeview(stops_frame, columns=columns, show='headings')
        self.stops_table.heading('stop_name', text='Название остановки')
        self.stops_table.heading('routes', text='Используется в маршрутах')
        self.stops_table.column('stop_name', width=200)
        self.stops_table.column('routes', width=300)
        self.stops_table.grid(column=0, row=0, sticky="NSEW")

        scrollbar = ttk.Scrollbar(stops_frame, orient=tk.VERTICAL, command=self.stops_table.yview)
        self.stops_table.configure(yscroll=scrollbar.set)
        scrollbar.grid(column=1, row=0, sticky='NS')

        self.stops_table.bind("<Double-1>", self.on_stop_double_click)

    def on_stop_double_click(self, event):
        region = self.stops_table.identify("region", event.x, event.y)
        if region != "cell":
            return

        column = self.stops_table.identify_column(event.x)
        item = self.stops_table.selection()[0]
        col_index = int(column[1:]) - 1

        if col_index == 0:
            self.edit_stop_name(item)
        elif col_index == 1:
            self.edit_stop_routes(item)

    def edit_stop_name(self, item):
        current_name = self.stops_table.item(item, 'values')[0]

        entry = ttk.Entry(self.stops_table)
        entry.insert(0, current_name)
        entry.bind("<FocusOut>", lambda e: self.save_stop_name(item, entry))
        entry.bind("<Return>", lambda e: self.save_stop_name(item, entry))

        bbox = self.stops_table.bbox(item, column='#1')
        entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])

    def save_stop_name(self, item, entry):
        new_name = entry.get().strip()
        entry.destroy()

        if not new_name or new_name == self.stops_table.item(item, 'values')[0]:
            return

        old_name = self.stops_table.item(item, 'values')[0]
        self.stops[self.stops.index(old_name)] = new_name
        self.stop_routes[new_name] = self.stop_routes.pop(old_name)

        for route in self.routes:
            if route['start'] == old_name:
                route['start'] = new_name
            if route['end'] == old_name:
                route['end'] = new_name
            if old_name in route['stops']:
                route['stops'][route['stops'].index(old_name)] = new_name

        self.update_stops_table()
        self.update_stops_combo()

    def edit_stop_routes(self, item):
        stop_name = self.stops_table.item(item, 'values')[0]
        current_routes = self.stop_routes.get(stop_name, [])

        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Управление маршрутами для {stop_name}")
        edit_window.geometry("400x400")

        main_frame = ttk.Frame(edit_window)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.route_controls = {}

        for route in self.routes:
            route_num = route['route_num']
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill='x', pady=2)

            var = tk.BooleanVar(value=route_num in current_routes)
            time_var = tk.StringVar(value=str(self.route_stops.get(route_num, {}).get(stop_name, 0)))

            cb = ttk.Checkbutton(
                frame,
                text=f"Маршрут {route_num}",
                variable=var,
                command=lambda rn=route_num: self.toggle_route_control(rn)
            )
            cb.pack(side='left', padx=5)

            time_entry = ttk.Entry(
                frame,
                textvariable=time_var,
                width=5,
                state='normal' if var.get() else 'disabled'
            )
            time_entry.pack(side='left', padx=5)
            ttk.Label(frame, text="мин").pack(side='left')

            self.route_controls[route_num] = {
                'var': var,
                'time_entry': time_var,
                'widget': time_entry
            }

        btn_frame = ttk.Frame(edit_window)
        btn_frame.pack(pady=10)

        ttk.Button(
            btn_frame,
            text="Сохранить",
            command=lambda: self.save_stop_routes(stop_name, edit_window)
        ).pack()

    def toggle_route_control(self, route_num):
        control = self.route_controls[route_num]
        if control['var'].get():
            control['widget'].config(state='normal')
        else:
            control['widget'].config(state='disabled')

    def save_stop_routes(self, stop_name, window):
        updated_routes = []

        for route_num, control in self.route_controls.items():
            if control['var'].get():
                try:
                    time = int(control['time_entry'].get())
                    updated_routes.append(route_num)

                    if route_num not in self.route_stops:
                        self.route_stops[route_num] = {}
                    self.route_stops[route_num][stop_name] = time

                except ValueError:
                    messagebox.showerror("Ошибка",
                                         f"Некорректное время для маршрута {route_num}")
                    return
            else:
                if route_num in self.stop_routes[stop_name]:
                    self.stop_routes[stop_name].remove(route_num)
                if route_num in self.route_stops and stop_name in self.route_stops[route_num]:
                    del self.route_stops[route_num][stop_name]

        self.stop_routes[stop_name] = updated_routes
        self.update_stops_table()
        window.destroy()
        messagebox.showinfo("Успех", "Изменения сохранены")

    def update_routes_table(self):
        for item in self.routes_table.get_children():
            self.routes_table.delete(item)

        for route in self.routes:
            self.routes_table.insert('', tk.END, values=(
                route['route_num'],
                route['start'],
                route['end'],
                len(route['stops']),
                route['travel_time'],
                route['busyness']
            ))

    def add_stop(self):
        stop_name = self.stop_name_entry.get().strip()
        if not stop_name:
            messagebox.showerror("Ошибка", "Введите название остановки")
            return

        if stop_name in self.stops:
            messagebox.showerror("Ошибка", f"Остановка '{stop_name}' уже существует")
            return

        self.stops.append(stop_name)
        self.stop_routes[stop_name] = []

        self.stops_table.insert('', tk.END, values=(stop_name, ""))
        self.update_stops_combo()

        self.stop_name_entry.delete(0, tk.END)
        messagebox.showinfo("Успех", f"Остановка '{stop_name}' добавлена")

    def delete_stop(self):
        selected_item = self.stops_table.selection()
        if not selected_item:
            messagebox.showinfo("Информация", "Выберите остановку для удаления")
            return

        item_values = self.stops_table.item(selected_item[0], 'values')
        stop_name = item_values[0]

        if stop_name in self.stop_routes and self.stop_routes[stop_name]:
            messagebox.showerror("Ошибка",
                                 f"Остановка '{stop_name}' используется в маршрутах. Удалите её из маршрутов сначала.")
            return

        self.stops.remove(stop_name)
        if stop_name in self.stop_routes:
            del self.stop_routes[stop_name]

        self.stops_table.delete(selected_item[0])
        self.update_stops_combo()

        messagebox.showinfo("Успех", f"Остановка '{stop_name}' удалена")

    def add_stop_to_route(self):
        stop_name = self.stop_for_route.get()
        route_num = self.route_for_stop.get()

        if not stop_name or not route_num:
            messagebox.showinfo("Информация", "Выберите остановку и маршрут")
            return

        if route_num not in [r['route_num'] for r in self.routes]:
            messagebox.showerror("Ошибка", f"Маршрут {route_num} не существует")
            return

        if stop_name not in self.stops:
            messagebox.showerror("Ошибка", f"Остановка '{stop_name}' не существует")
            return

        if route_num not in self.stop_routes[stop_name]:
            self.stop_routes[stop_name].append(route_num)
            self.update_stops_table()
            messagebox.showinfo("Успех", f"Остановка '{stop_name}' добавлена в маршрут {route_num}")
        else:
            messagebox.showinfo("Информация", f"Остановка '{stop_name}' уже включена в маршрут {route_num}")

    def remove_stop_from_route(self):
        stop_name = self.stop_for_route.get()
        route_num = self.route_for_stop.get()

        if not stop_name or not route_num:
            messagebox.showinfo("Информация", "Выберите остановку и маршрут")
            return

        if route_num in self.stop_routes[stop_name]:
            self.stop_routes[stop_name].remove(route_num)
            self.update_stops_table()
            messagebox.showinfo("Успех", f"Остановка '{stop_name}' удалена из маршрута {route_num}")
        else:
            messagebox.showinfo("Информация", f"Остановка '{stop_name}' не входит в маршрут {route_num}")

    def update_stops_table(self):
        for item in self.stops_table.get_children():
            self.stops_table.delete(item)

        for stop in self.stops:
            routes_list = ", ".join(self.stop_routes[stop]) if stop in self.stop_routes else ""
            self.stops_table.insert('', tk.END, values=(stop, routes_list))

    def update_stops_combo(self):
        self.stops.sort()
        self.start_stop['values'] = self.stops
        self.end_stop['values'] = self.stops
        if hasattr(self, 'stop_combobox'):
            self.stop_combobox['values'] = self.stops
        self.stops_listbox.delete(0, tk.END)
        for stop in self.stops:
            self.stops_listbox.insert(tk.END, stop)

    def update_route_combo(self):
        route_nums = [route['route_num'] for route in self.routes]
        self.route_for_viz['values'] = route_nums
        self.route_for_stop['values'] = route_nums
        if route_nums:
            self.route_for_viz.current(0)
            self.route_for_stop.current(0)

    def setup_schedule_by_stop_tab(self):
        frame = ttk.LabelFrame(self.tab5, text="Расписание по остановке")
        frame.grid(column=0, row=0, padx=10, pady=10, sticky="NSEW")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        ttk.Label(frame, text="Выберите остановку:").grid(column=0, row=0, padx=5, pady=5, sticky="w")
        self.stop_combobox = ttk.Combobox(frame, values=self.stops, width=30)
        self.stop_combobox.grid(column=1, row=0, padx=5, pady=5, sticky="ew")

        ttk.Button(frame, text="Показать расписание", command=self.show_stop_schedule) \
            .grid(column=2, row=0, padx=5, pady=5)

        columns = ('route', 'arrival')
        self.schedule_tree = ttk.Treeview(
            frame,
            columns=columns,
            show='headings',
            height=10
        )
        self.schedule_tree.heading('route', text='Маршрут')
        self.schedule_tree.heading('arrival', text='Прибытие')

        self.schedule_tree.column('route', width=100, anchor='center')
        self.schedule_tree.column('arrival', width=120, anchor='center')

        self.schedule_tree.grid(column=0, row=1, columnspan=3, padx=5, pady=5, sticky="nsew")

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.schedule_tree.yview)
        self.schedule_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(column=3, row=1, sticky='ns')

    def show_stop_schedule(self):
        selected_stop = self.stop_combobox.get()
        if not selected_stop:
            messagebox.showwarning("Ошибка", "Выберите остановку")
            return

        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)

        schedule_data = []
        for route_num in self.stop_routes.get(selected_stop, []):
            route_schedule = self.schedules.get(route_num, [])
            time_to_stop = self.route_stops.get(route_num, {}).get(selected_stop, 0)

            for trip in route_schedule:
                try:
                    departure = datetime.strptime(trip['departure'], "%H:%M")
                    arrival = departure + timedelta(minutes=time_to_stop)
                    schedule_data.append((
                        route_num,
                        arrival.strftime("%H:%M")
                    ))
                except ValueError:
                    continue

        schedule_data.sort(key=lambda x: datetime.strptime(x[1], "%H:%M"))

        for item in schedule_data:
            self.schedule_tree.insert('', 'end', values=item)

    def add_route(self):
        try:
            route_num = self.route_number.get()
            start = self.start_stop.get()
            end = self.end_stop.get()

            selected_stops = [self.stops_listbox.get(i) for i in self.stops_listbox.curselection()]

            travel_time = int(self.travel_time.get())
            busyness = int(self.busyness.get())

            if not route_num or not start or not end or not travel_time:
                messagebox.showerror("Ошибка", "Заполните все необходимые поля")
                return

            if start not in self.stops or end not in self.stops:
                messagebox.showerror("Ошибка", "Начальная или конечная остановка не существует")
                return

            stop_times = {}
            if route_num in self.route_stops:
                stop_times = self.route_stops[route_num]

            route_data = {
                'route_num': route_num,
                'start': start,
                'end': end,
                'stops': selected_stops,
                'stop_times': stop_times,
                'travel_time': travel_time,
                'busyness': busyness
            }

            if self.editing_index is not None:
                old_route_num = self.routes[self.editing_index]['route_num']
                self.routes[self.editing_index] = route_data

                for stop in self.stops:
                    if old_route_num in self.stop_routes[stop]:
                        self.stop_routes[stop].remove(old_route_num)

                self.stop_routes[start].append(route_num)
                self.stop_routes[end].append(route_num)
                for stop in selected_stops:
                    if route_num not in self.stop_routes[stop]:
                        self.stop_routes[stop].append(route_num)

                selected_item = self.routes_table.selection()[0]
                self.routes_table.item(selected_item, values=(
                    route_num,
                    start,
                    end,
                    len(selected_stops),
                    travel_time,
                    busyness
                ))

                self.add_button.configure(text="Добавить маршрут")
                self.editing_index = None
                messagebox.showinfo("Успех", f"Маршрут {route_num} обновлен")
            else:
                if any(r['route_num'] == route_num for r in self.routes):
                    messagebox.showerror("Ошибка", f"Маршрут с номером {route_num} уже существует")
                    return

                self.routes.append(route_data)

                self.stop_routes[start].append(route_num)
                self.stop_routes[end].append(route_num)
                for stop in selected_stops:
                    if route_num not in self.stop_routes[stop]:
                        self.stop_routes[stop].append(route_num)

                self.routes_table.insert('', tk.END, values=(
                    route_num,
                    start,
                    end,
                    len(selected_stops),
                    travel_time,
                    busyness
                ))

                messagebox.showinfo("Успех", f"Маршрут {route_num} добавлен")

            self.route_stops[route_num] = stop_times
            self.update_route_combo()
            self.update_stops_table()

            self.route_number.delete(0, tk.END)
            self.start_stop.set('')
            self.end_stop.set('')
            self.stops_listbox.selection_clear(0, tk.END)
            self.travel_time.delete(0, tk.END)
            self.busyness.set(1)
        except ValueError as e:
            messagebox.showerror("Ошибка", "Заполните все необходимые поля")

    def edit_route(self):
        selected_item = self.routes_table.selection()
        if not selected_item:
            messagebox.showinfo("Информация", "Выберите маршрут для редактирования")
            return

        item_values = self.routes_table.item(selected_item[0], 'values')
        route_num = item_values[0]

        for i, route in enumerate(self.routes):
            if route['route_num'] == route_num:
                self.editing_index = i
                route_data = route
                break

        self.route_number.delete(0, tk.END)
        self.route_number.insert(0, route_data['route_num'])

        self.start_stop.set(route_data['start'])
        self.end_stop.set(route_data['end'])

        self.stops_listbox.selection_clear(0, tk.END)
        for stop in route_data['stops']:
            try:
                idx = self.stops.index(stop)
                self.stops_listbox.selection_set(idx)
            except ValueError:
                pass

        self.travel_time.delete(0, tk.END)
        self.travel_time.insert(0, str(route_data['travel_time']))

        self.busyness.set(route_data['busyness'])

        self.add_button.configure(text="Сохранить изменения")

    def delete_route(self):
        selected_item = self.routes_table.selection()
        if not selected_item:
            messagebox.showinfo("Информация", "Выберите маршрут для удаления")
            return

        item_values = self.routes_table.item(selected_item[0], 'values')
        route_num = item_values[0]

        self.routes = [r for r in self.routes if r['route_num'] != route_num]

        self.routes_table.delete(selected_item[0])

        if self.editing_index is not None:
            if route_num == self.routes[self.editing_index]['route_num']:
                self.editing_index = None
                self.add_button.configure(text="Добавить маршрут")

                self.route_number.delete(0, tk.END)
                self.start_stop.delete(0, tk.END)
                self.end_stop.delete(0, tk.END)
                self.intermediate_stops.delete("1.0", tk.END)
                self.travel_time.delete(0, tk.END)
                self.busyness.set(1)

        self.update_route_combo()

        messagebox.showinfo("Информация", f"Маршрут {route_num} удален")

    def load_example(self):
        example_stops = [
            'Автостанция Электрогорск',
            'Улица Кржижановского / Советская улица',
            'Школа №16',
            'Рабочий посёлок / Общежитие',
            'Мебельный комбинат',
            'Поворот на Электрогорск / 75-й км',
            'Сады «73 км»',
            'Кузнецы',
            'Улица Новая',
            'Заозерье-2',
            'Заозерье-1',
            'Андроново',
            'Льнокомбинат',
            'Администрация',
            'Новостройка',
            'Школа №11',
            'Улица Маяковского',
            'Автодор',
            'Улица Автомобилистов',
            'Улица Мира',
            'Школа №18',
            'Площадь Революции',
            'Аптека',
            'Большие дома',
            'Улица Герцена',
            'Автовокзал Павловский Посад',
            'Кузнецы - 2',
            'Тарасово',
            'Керамический завод',
            'Фабрика',
            'Богослово',
            'Совхоз',
            'РТС',
            'Бензоколонка',
            'Птицефабрика',
            'Успенск',
            'Владимирская улица',
            'Автоколонна №1783',
            'ПОГАТ',
            'Инкубатор',
            'Новые дома',
            'Нарсуд',
            'Кинотеатр «Рассвет»',
            'Ногинск, автовокзал',
            'Эколаб',
            'Элеон',
            'Ферейн',
            'Белый Мох',
            'Бетонка / Электрогорск, поворот',
            '3-й км',
            'Никулино, поворот',
            'Кирпичный завод',
            'Малая Дубна / Орехово-Зуево, поворот',
            'Кладбище',
            'Автоколонна №1793',
            'Интернат',
            'Детский мир',
            'Магазин «Овощи»',
            'Завод «Респиратор»',
            'Сквер Ленина',
            'Автовокзал Орехово-Зуево',
            'Псарьки',
            'Фабрика им. Ленина, трасса',
            'Купавинский поворот',
            'Зеленый',
            'Южный квартал',
            'Горсовет',
            'м. Партизанская'
        ]

        self.stops = []
        self.stop_routes = {}
        self.routes = []
        self.route_stops = {}
        self.routes_table.delete(*self.routes_table.get_children())
        self.stops_table.delete(*self.stops_table.get_children())

        for stop in example_stops:
            self.stops.append(stop)
            self.stop_routes[stop] = []

        route21_stops = [
            'Улица Кржижановского / Советская улица',
            'Школа №16',
            'Рабочий посёлок / Общежитие',
            'Мебельный комбинат',
            'Поворот на Электрогорск / 75-й км',
            'Сады «73 км»',
            'Кузнецы',
            'Улица Новая',
            'Заозерье-2',
            'Заозерье-1',
            'Андроново',
            'Льнокомбинат',
            'Администрация',
            'Новостройка',
            'Школа №11',
            'Улица Маяковского',
            'Автодор',
            'Улица Автомобилистов',
            'Улица Мира',
            'Школа №18',
            'Площадь Революции',
            'Аптека',
            'Большие дома',
            'Улица Герцена'
        ]
        self.routes.append({
            'route_num': '21',
            'start': 'Автостанция Электрогорск',
            'end': 'Автовокзал Павловский Посад',
            'stops': route21_stops,
            'travel_time': 51,
            'busyness': 8
        })
        self.route_stops['21'] = {
            'Улица Кржижановского / Советская улица': 1,
            'Школа №16': 2,
            'Рабочий посёлок / Общежитие': 4,
            'Мебельный комбинат': 5,
            'Поворот на Электрогорск / 75-й км': 9,
            'Сады «73 км»': 12,
            'Кузнецы': 17,
            'Улица Новая': 18,
            'Заозерье-2': 20,
            'Заозерье-1': 23,
            'Андроново': 25,
            'Льнокомбинат': 27,
            'Администрация': 28,
            'Новостройка': 30,
            'Школа №11': 32,
            'Улица Маяковского': 33,
            'Автодор': 37,
            'Улица Автомобилистов': 37,
            'Улица Мира': 39,
            'Школа №18': 41,
            'Площадь Революции': 42,
            'Аптека': 45,
            'Большие дома': 47,
            'Улица Герцена': 49,
            'Автовокзал Павловский Посад': 51
        }

        route26_stops = [
            'Улица Кржижановского / Советская улица',
            'Школа №16',
            'Рабочий посёлок / Общежитие',
            'Мебельный комбинат',
            'Поворот на Электрогорск / 75-й км',
            'Сады «73 км»',
            'Кузнецы - 2',
            'Кузнецы',
            'Тарасово',
            'Новостройка',
            'Керамический завод',
            'Фабрика',
            'Богослово',
            'Совхоз',
            'Бензоколонка',
            'Птицефабрика',
            'Успенск',
            'Владимирская улица',
            'Автоколонна №1783',
            'ПОГАТ',
            'Инкубатор',
            'Новые дома',
            'Нарсуд',
            'Кинотеатр «Рассвет»'
        ]
        self.routes.append({
            'route_num': '26',
            'start': 'Автостанция Электрогорск',
            'end': 'Ногинск, автовокзал',
            'stops': route26_stops,
            'travel_time': 50,
            'busyness': 7
        })
        self.route_stops['26'] = {
            'Улица Кржижановского / Советская улица': 1,
            'Школа №16': 3,
            'Рабочий посёлок / Общежитие': 5,
            'Мебельный комбинат': 6,
            'Поворот на Электрогорск / 75-й км': 8,
            'Сады «73 км»': 11,
            'Кузнецы - 2': 18,
            'Кузнецы': 19,
            'Тарасово': 20,
            'Новостройка': 21,
            'Керамический завод': 23,
            'Фабрика': 25,
            'Богослово': 28,
            'Совхоз': 29,
            'Бензоколонка': 30,
            'Птицефабрика': 33,
            'Успенск': 35,
            'Владимирская улица': 36,
            'Автоколонна №1783': 37,
            'ПОГАТ': 38,
            'Инкубатор': 40,
            'Новые дома': 41,
            'Нарсуд': 43,
            'Кинотеатр «Рассвет»': 45,
            'Ногинск, автовокзал': 50
        }
        route58_stops = [
            'Эколаб',
            'Элеон',
            'Ферейн',
            'Белый Мох',
            'Бетонка / Электрогорск, поворот',
            '3-й км',
            'Никулино, поворот',
            'Птицефабрика',
            'Кирпичный завод',
            'Малая Дубна / Орехово-Зуево, поворот',
            'Кладбище',
            'Совхоз',
            'РТС',
            'Автоколонна №1793',
            'ПОГАТ',
            'Интернат',
            'Детский мир',
            'Магазин «Овощи»',
            'Завод «Респиратор»',
            'Сквер Ленина'
        ]
        self.routes.append({
            'route_num': '58',
            'start': 'Автостанция Электрогорск',
            'end': 'Автовокзал Орехово-Зуево',
            'stops': route58_stops,
            'travel_time': 50,
            'busyness': 6
        })
        self.route_stops['58'] = {
            'Эколаб': 1,
            'Элеон': 2,
            'Ферейн': 5,
            'Белый Мох': 9,
            'Бетонка / Электрогорск, поворот': 11,
            '3-й км': 15,
            'Никулино, поворот': 19,
            'Птицефабрика': 22,
            'Кирпичный завод': 23,
            'Малая Дубна / Орехово-Зуево, поворот': 24,
            'Кладбище': 30,
            'Совхоз': 31,
            'РТС': 34,
            'Автоколонна №1793': 35,
            'ПОГАТ': 35,
            'Интернат': 37,
            'Детский мир': 39,
            'Магазин «Овощи»': 41,
            'Завод «Респиратор»': 43,
            'Сквер Ленина': 47,
            'Автовокзал Орехово-Зуево': 50
        }

        route375_stops = [
            'Улица Кржижановского / Советская улица',
            'Школа №16',
            'Рабочий посёлок / Общежитие',
            'Мебельный комбинат',
            'Поворот на Электрогорск / 75-й км',
            'Сады «73 км»',
            'Кузнецы',
            'Тарасово',
            'Новостройка',
            'Керамический завод',
            'Фабрика',
            'Богослово',
            'Псарьки',
            'Фабрика им. Ленина, трасса',
            'Купавинский поворот',
            'Зеленый',
            'Южный квартал',
            'Горсовет'
        ]
        self.routes.append({
            'route_num': '375',
            'start': 'Автостанция Электрогорск',
            'end': 'м. Партизанская',
            'stops': route375_stops,
            'travel_time': 95,
            'busyness': 4
        })
        self.route_stops['375'] = {
            'Улица Кржижановского / Советская улица': 1,
            'Школа №16': 1,
            'Рабочий посёлок / Общежитие': 2,
            'Мебельный комбинат': 3,
            'Поворот на Электрогорск / 75-й км': 5,
            'Сады «73 км»': 7,
            'Кузнецы': 14,
            'Тарасово': 15,
            'Новостройка': 16,
            'Керамический завод': 17,
            'Фабрика': 19,
            'Богослово': 21,
            'Псарьки': 44,
            'Фабрика им. Ленина, трасса': 49,
            'Купавинский поворот': 51,
            'Зеленый': 55,
            'Южный квартал': 58,
            'Горсовет': 62,
            'м. Партизанская': 95
        }

        for route in self.routes:
            self.routes_table.insert('', tk.END, values=(
                route['route_num'],
                route['start'],
                route['end'],
                len(route['stops']),
                route['travel_time'],
                route['busyness']
            ))

            self.stop_routes[route['start']].append(route['route_num'])
            self.stop_routes[route['end']].append(route['route_num'])
            for stop in route['stops']:
                self.stop_routes[stop].append(route['route_num'])

        self.update_stops_table()
        self.update_stops_combo()
        self.update_route_combo()
        messagebox.showinfo("Информация", "Загружены примеры 4 маршрутов с остановками")

    def update_route_combo(self):
        route_nums = [route['route_num'] for route in self.routes]
        self.route_for_viz['values'] = route_nums
        if route_nums:
            self.route_for_viz.current(0)

    def optimize_schedule(self):
        if not self.routes:
            messagebox.showinfo("Информация", "Сначала добавьте маршруты")
            return

        try:
            start_hour = int(self.start_hour.get())
            end_hour = int(self.end_hour.get())
            buses_count = int(self.buses_count.get())

            if start_hour >= end_hour:
                messagebox.showerror("Ошибка", "Время начала должно быть меньше времени окончания")
                return

            morning_peak = 'selected' in self.morning_peak.state()
            evening_peak = 'selected' in self.evening_peak.state()

            self.optimization_result.delete("1.0", tk.END)

            self.schedules = self.ai_optimize_schedule(
                self.routes,
                start_hour,
                end_hour,
                buses_count,
                morning_peak,
                evening_peak
            )

            self.display_optimization_results()

        except ValueError as e:
            messagebox.showerror("Ошибка", f"Неверный формат данных: {e}")

    def ai_optimize_schedule(self, routes, start_hour, end_hour, buses_count, morning_peak, evening_peak):
        schedules = {}
        stop_times = {}
        min_interval = int(self.min_interval.get())

        total_working_minutes = (end_hour - start_hour) * 60
        absolute_min_trips = total_working_minutes // min_interval

        total_busyness = sum(r['busyness'] for r in routes)
        route_weights = {r['route_num']: r['busyness'] / total_busyness for r in routes}

        max_trips = min(absolute_min_trips, buses_count * 10)
        route_trips = {
            r['route_num']: max(1, int(max_trips * route_weights[r['route_num']]))
            for r in routes
        }

        total_allocated = sum(route_trips.values())
        if total_allocated > max_trips:
            reduction_factor = max_trips / total_allocated
            for route_num in route_trips:
                route_trips[route_num] = max(1, int(route_trips[route_num] * reduction_factor))

        for route in routes:
            route_num = route['route_num']
            travel_time = route['travel_time']
            target_trips = route_trips[route_num]

            base_interval = total_working_minutes / target_trips
            schedule = []
            current_time = datetime.strptime(f"{start_hour}:00", "%H:%M")
            end_time = datetime.strptime(f"{end_hour}:00", "%H:%M")

            all_stops = [route['start']] + route['stops'] + [route['end']]
            for stop in all_stops:
                if stop not in stop_times:
                    stop_times[stop] = []

            trip_count = 0
            while current_time < end_time and trip_count < target_trips:
                hour = current_time.hour
                is_peak = (morning_peak and 7 <= hour < 9) or (evening_peak and 17 <= hour < 19)
                interval = max(base_interval * (0.6 if is_peak else 1.0), min_interval)

                departure_time = current_time
                valid = True

                for stop in all_stops:
                    stop_delay = self.route_stops[route_num].get(stop,
                                                                 0 if stop == route['start'] else travel_time)
                    arrival_time = departure_time + timedelta(minutes=stop_delay)

                    for existing in stop_times[stop]:
                        if existing['route'] == route_num:
                            time_diff = abs((arrival_time -
                                             datetime.strptime(existing['time'], "%H:%M")).total_seconds() / 60)
                            if time_diff < min_interval:
                                valid = False
                                break
                    if not valid:
                        break

                if valid:
                    schedule.append({
                        'departure': departure_time.strftime("%H:%M"),
                        'arrival': (departure_time +
                                    timedelta(minutes=travel_time)).strftime("%H:%M"),
                        'travel_time': travel_time
                    })
                    trip_count += 1

                    for stop in all_stops:
                        stop_delay = self.route_stops[route_num].get(stop,
                                                                     0 if stop == route['start'] else travel_time)
                        stop_time = departure_time + timedelta(minutes=stop_delay)
                        stop_times[stop].append({
                            'time': stop_time.strftime("%H:%M"),
                            'route': route_num
                        })

                    current_time += timedelta(minutes=interval)
                else:
                    current_time += timedelta(minutes=1)

            schedules[route_num] = schedule[1::]

        return schedules

    def display_optimization_results(self):
        if not self.schedules:
            return

        result_text = "Оптимизированное расписание автобусов:\n\n"

        for route_num, schedule in self.schedules.items():
            route_data = next((r for r in self.routes if r['route_num'] == route_num), None)

            result_text += f"Маршрут №{route_num}: {route_data['start']} → {route_data['end']}\n"
            result_text += f"Время в пути: {route_data['travel_time']} мин. Загруженность: {route_data['busyness']}/10\n"
            result_text += "Отправление\tПрибытие\n"
            result_text += "-" * 30 + "\n"

            for trip in schedule:
                result_text += f"{trip['departure']}\t\t{trip['arrival']}\n"

            result_text += f"\nВсего рейсов: {len(schedule)}\n\n"
            result_text += "=" * 40 + "\n\n"

        self.optimization_result.insert(tk.END, result_text)

    def visualize_schedule(self):
        selected_route = self.route_for_viz.get()

        if not selected_route or selected_route not in self.schedules:
            messagebox.showinfo("Информация", "Выберите маршрут и проведите оптимизацию")
            return

        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        schedule = self.schedules[selected_route]

        departures = []
        for trip in schedule:
            h, m = map(int, trip['departure'].split(':'))
            departures.append(h + m / 60)

        fig = Figure(figsize=(6, 6))

        ax1 = fig.add_subplot(211)

        hour_counts = {}
        for dep in departures:
            hour = int(dep)
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        hours = sorted(hour_counts.keys())
        counts = [hour_counts[h] for h in hours]

        ax1.bar(hours, counts, color='skyblue')
        ax1.set_xlabel('Час')
        ax1.set_ylabel('Количество рейсов')
        ax1.set_title(f'Распределение рейсов по часам (Маршрут {selected_route})')
        ax1.set_xticks(range(min(hours), max(hours) + 1))
        ax1.grid(axis='y', linestyle='--', alpha=0.7)
        ax1.yaxis.set_major_locator(MaxNLocator(integer=True))

        ax2 = fig.add_subplot(212)

        if len(departures) > 1:
            intervals = []
            for i in range(1, len(departures)):
                intervals.append((departures[i] - departures[i - 1]) * 60)

            ax2.plot(range(1, len(departures)), intervals, marker='o', linestyle='-', color='green')
            ax2.set_xlabel('Номер рейса')
            ax2.set_ylabel('Интервал (мин)')
            ax2.set_title('Интервалы между автобусами')
            ax2.grid(True, linestyle='--', alpha=0.7)

            avg_interval = sum(intervals) / len(intervals)
            ax2.axhline(y=avg_interval, color='r', linestyle='--', label=f'Средний интервал: {avg_interval:.1f} мин')
            ax2.legend()

        fig.tight_layout()
        ax2.yaxis.set_major_locator(MaxNLocator(integer=True))

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack()


if __name__ == "__main__":
    root = tk.Tk()
    app = BusScheduleOptimizer(root)
    root.mainloop()
