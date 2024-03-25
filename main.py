import tkinter as tk
import numpy as np
from tkinter import ttk


class Application(tk.Tk):
    def __init__(self):

        super().__init__()

        self.title('smallCAD')

        min_height = 500
        min_width = int(min_height / 9 * 16)
        self.minsize(min_width, min_height)

        self.iconbitmap('cadicon.ico')

        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=20)
        self.rowconfigure(2, weight=0)
        self.columnconfigure(0, weight=1)

        workspace = WorkSpaceManager(self)
        self.managers = {'toolbar': ToolBarManager(self, workspace),
                         'workspace': workspace,
                         'bottombar': BottomBarManager(self, workspace)}

        for i, frame in enumerate(self.managers.values()):
            frame.grid(row=i, column=0, sticky='nsew')

        self.update()
        self.managers['workspace'].setCenter()


class ToolBarManager(tk.Frame):
    def __init__(self, root, workspace):
        super().__init__(root, name='toolbar')
        for i in range(1, 8):
            self.columnconfigure(i, weight=1)

        self.workspace_slave = workspace

        self.buttons = {'line': tk.Button(self, text='Line', width=17, height=2, name='line_btn',
                                          command=lambda: self.showPopup('line'))}
        self.buttons['line'].grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

        self.popups = {'line': tk.Menu(self, tearoff=0)}
        for line_type in WorkSpaceManager.LINE_TYPE_THICKNESS.keys():
            self.popups['line'].add_command(label=line_type.capitalize(),
                                            command=lambda type_=line_type: self.showLineSubMenu(type_))

    def showPopup(self, type_):
        self.popups[type_].tk_popup(self.buttons[type_].winfo_rootx(),
                                    self.buttons[type_].winfo_rooty() + self.buttons[type_].winfo_height())

    def showLineSubMenu(self, type_):
        self.buttons['line']['state'] = tk.DISABLED
        self.workspace_slave.showLineSubMenu(type_)
        pass


class WorkSpaceManager(tk.Frame):
    BASE_THICKNESS_SCOPE = [0.5, 1.4]
    PIXEL_SCALE = 0.25
    LINE_TYPE_THICKNESS = {'continuous': 1.0, 'continuous thin': 0.5,
                           'dashed': 0.5, 'chain': 0.5, 'chain thick': 2.0 / 3.0}
    LINE_TYPE_DASH = {'dashed': [2.0, 8.0], 'chain': [5.0, 30.0], 'chain thick': [3.0, 8.0]}
    LINE_TYPE_SPACE = {'dashed': [1.0, 2.0], 'chain': [3.0, 5.0], 'chain thick': [3.0, 4.0]}

    def __init__(self, root):
        super().__init__(root, bg='white')
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(self, bg='white', highlightbackground='#fafafa')
        self.canvas.grid(row=0, column=0, sticky='nsew')

        self.sub_menu = tk.Frame(self, bg='#fafafa')
        for i in range(10):
            self.sub_menu.rowconfigure(i, weight=0)
        self.sub_menu.rowconfigure(10, weight=1)

        self.base_thickness = 1.0
        self.center = None

        self.obj_movement = ObjectMovementHandler(self)

    def setCenter(self):
        self.center = np.array([int(np.ceil(self.winfo_width() / 2)),
                                int(np.ceil(self.winfo_height() / 2))])
        self.canvas.create_line(self.center[0] - 15, self.center[1], self.center[0] + 15, self.center[1], width=2,
                                fill='red')
        self.canvas.create_line(self.center[0], self.center[1] - 15, self.center[0], self.center[1] + 15, width=2,
                                fill='red')

    def updateThickness(self, thickness):
        self.base_thickness = thickness
        for line_id in self.canvas.find_all():
            if len(self.canvas.gettags(line_id)) != 0:
                found_tag = self.canvas.gettags(line_id)[0]
                if found_tag in WorkSpaceManager.LINE_TYPE_THICKNESS.keys():
                    self.canvas.itemconfig(line_id,
                                           width=self.base_thickness
                                           * WorkSpaceManager.LINE_TYPE_THICKNESS[found_tag]
                                           / WorkSpaceManager.PIXEL_SCALE)

    def showLineSubMenu(self, type_):
        for child in self.sub_menu.winfo_children():
            child.destroy()

        line = Line(type_)

        elements = []
        if type_ not in ['continuous', 'continuous thin']:
            elements.append(tk.Label(self.sub_menu, text='Dash', anchor='center', bg='#fafafa'))
            elements.append(tk.Scale(self.sub_menu, orient=tk.HORIZONTAL, resolution=0.05, name='dash', bg='#fafafa',
                                     highlightbackground='#fafafa',
                                     from_=WorkSpaceManager.LINE_TYPE_DASH[type_][0],
                                     to=WorkSpaceManager.LINE_TYPE_DASH[type_][1]))
            elements.append(tk.Label(self.sub_menu, text='Space', anchor='center', bg='#fafafa'))
            elements.append(tk.Scale(self.sub_menu, orient=tk.HORIZONTAL, resolution=0.05, name='space', bg='#fafafa',
                                     highlightbackground='#fafafa',
                                     from_=WorkSpaceManager.LINE_TYPE_SPACE[type_][0],
                                     to=WorkSpaceManager.LINE_TYPE_SPACE[type_][1]))

        elements.append(ttk.OptionMenu(self.sub_menu, tk.StringVar(), 'Cartesian', *['Cartesian', 'Polar'],
                                       command=self.changeCoordType))

        for i, element in enumerate(elements):
            element.grid(row=i, column=0, columnspan=2, sticky='ew', padx=5)
            if i in (0, 2, 4):
                element.grid_configure(pady=(15, 0))

        for i, row in enumerate([['X0', 'Y0'], ['X1', 'Y1']]):
            for j, el in enumerate(row):
                label = tk.Label(self.sub_menu, text=el, anchor='center', bg='#fafafa', name=el.lower())
                input_ = tk.Entry(self.sub_menu, width=10, bg='#fafafa', name=el.lower() + '_i')
                label.grid(row=i * 2 + 5, column=j, sticky='nsew', pady=(10, 0))
                input_.grid(row=i * 2 + 5 + 1, column=j, sticky='nsew', padx=5)

        accept_btn = tk.Button(self.sub_menu, text='Create', command=lambda: self.createLine(line), name='accept')
        accept_btn.grid(row=9, column=0, columnspan=2, pady=(15, 0), padx=10, sticky='nsew')

        self.sub_menu.grid(row=0, column=1, sticky='nsew')

        self.canvas.bind('<Button-1>', lambda event: self.chooseLinePoints(event, line))
        self.canvas.bind('<Button-3>', lambda event: self.canselPoint(line))

    def changeCoordType(self, value):
        text_mapping = {'X1': 'Φ', 'Y1': 'R'} if value == 'Polar' else {'Φ': 'X1', 'R': 'Y1'}
        for widget in self.sub_menu.winfo_children():
            try:
                widget['text'] = text_mapping.get(widget['text'], widget['text'])
            except tk.TclError:
                continue

    def createLine(self, line):
        thickness_px = int(self.base_thickness
                           * WorkSpaceManager.LINE_TYPE_THICKNESS[line.type] / WorkSpaceManager.PIXEL_SCALE)
        coord_type = None
        dash = None
        space = None

        self.canvas.unbind('<Button-1>')
        self.canvas.unbind('<Button-3>')

        for widget in self.sub_menu.winfo_children():
            if isinstance(widget, ttk.OptionMenu):
                coord_type = self.sub_menu.getvar(name=widget.cget('textvariable'))
            elif widget.winfo_name() == 'dash':
                dash = widget.get()
            elif widget.winfo_name() == 'space':
                space = widget.get()

        if np.all(np.isinf(line.points[1])):
            for widget in self.sub_menu.winfo_children():
                if np.isinf(line.points[0][0]) or np.isinf(line.points[0][1]):
                    if widget.winfo_name() == 'x0_i':
                        line.points[0][0] = float(widget.get())
                    elif widget.winfo_name() == 'y0_i':
                        line.points[0][1] = float(widget.get())
                else:
                    if widget.winfo_name() == 'x1_i':
                        line.points[1][0] = float(widget.get())
                    elif widget.winfo_name() == 'y1_i':
                        line.points[1][1] = float(widget.get())

        self.sub_menu.grid_forget()
        for child in self.sub_menu.winfo_children():
            child.destroy()

        self.canvas.delete("confirm_btn", "new_line_0", "new_line_1")

        if coord_type == 'Polar':
            line.points[1] = (line.points[0][0] + line.points[1][1] * np.cos(line.points[1][0]),
                              line.points[0][1] + line.points[1][1] * np.sin(line.points[1][0]))

        line.points[0][0] += self.center[0]
        line.points[0][1] = self.center[1] - line.points[0][1]
        line.points[1][0] += self.center[0]
        line.points[1][1] = self.center[1] - line.points[1][1]

        if line.type in ['continuous', 'continuous thin']:
            self.canvas.create_line(*line.points.flatten(), width=thickness_px, tags=(line.type,))
        else:
            dash_px = (dash / WorkSpaceManager.PIXEL_SCALE)
            space_px = (space / WorkSpaceManager.PIXEL_SCALE)

            distance = np.sqrt(
                (line.points[1][0] - line.points[0][0]) ** 2 + (line.points[1][1] - line.points[0][1]) ** 2)

            dir_x = (line.points[1][0] - line.points[0][0]) / distance
            dir_y = (line.points[1][1] - line.points[0][1]) / distance

            current_pos = line.points[0]

            if line.type == 'dashed':
                while distance > dash_px + space_px:
                    dash_end = [current_pos[0] + dir_x * dash_px,
                                current_pos[1] + dir_y * dash_px]

                    self.canvas.create_line(*current_pos, *dash_end, width=thickness_px, tags=(line.type,))

                    current_pos = [dash_end[0] + dir_x * space_px,
                                   dash_end[1] + dir_y * space_px]

                    distance -= (dash_px + space_px)
            else:
                space_minus_dot_px = (space_px - 2) / 2
                while distance > dash_px + space_px:
                    dash_end = [current_pos[0] + dir_x * dash_px,
                                current_pos[1] + dir_y * dash_px]

                    self.canvas.create_line(*current_pos, *dash_end, width=thickness_px, tags=(line.type,))

                    dot_start = (dash_end[0] + dir_x * space_minus_dot_px,
                                 dash_end[1] + dir_y * space_minus_dot_px)
                    dot_end = (dot_start[0] + dir_x * 2,
                               dot_start[1] + dir_y * 2)

                    self.canvas.create_line(dot_start, dot_end, width=thickness_px, tags=(line.type,))

                    current_pos = [dot_end[0] + dir_x * space_minus_dot_px,
                                   dot_end[1] + dir_y * space_minus_dot_px]

                    distance -= (dash_px + space_px)

            if distance > 0:
                self.canvas.create_line(*current_pos, *line.points[1], width=thickness_px, tags=(line.type,))

        for child in self.master.winfo_children():
            if child.winfo_name() == 'toolbar':
                for btn in child.winfo_children():
                    try:
                        btn['state'] = 'normal'
                    except tk.TclError:
                        continue

    def chooseLinePoints(self, event, line):
        if np.all(np.isinf(line.points[0])):
            self.canvas.create_oval(event.x + 3, event.y - 3,
                                    event.x - 3, event.y + 3, fill="black",
                                    tags="new_line_" + '0')
            line.points[0] = (event.x - self.center[0], self.center[1] - event.y)
            for widget in self.sub_menu.winfo_children():
                if widget.winfo_name() == 'x0_i':
                    widget.delete(0, 'end')
                    widget.insert(0, line.points[0][0])
                    widget['state'] = 'disabled'
                elif widget.winfo_name() == 'y0_i':
                    widget.delete(0, 'end')
                    widget.insert(0, line.points[0][1])
                    widget['state'] = 'disabled'
        elif np.all(np.isinf(line.points[1])):
            self.canvas.create_oval(event.x + 3, event.y - 3,
                                    event.x - 3, event.y + 3, fill="black",
                                    tags="new_line_" + '1')
            line.points[1] = (event.x - self.center[0], self.center[1] - event.y)
            for widget in self.sub_menu.winfo_children():
                if isinstance(widget, ttk.OptionMenu):
                    self.sub_menu.setvar(name=widget.cget('textvariable'), value='Cartesian')
                    self.changeCoordType('Cartesian')
                    widget['state'] = 'disabled'
            for widget in self.sub_menu.winfo_children():
                if widget.winfo_name() == 'x1_i':
                    widget.delete(0, 'end')
                    widget.insert(0, line.points[1][0])
                    widget['state'] = 'disabled'
                elif widget.winfo_name() == 'y1_i':
                    widget.delete(0, 'end')
                    widget.insert(0, line.points[1][1])
                    widget['state'] = 'disabled'
                elif widget.winfo_name() == 'accept':
                    widget['state'] = 'disabled'

            confirm_btn = tk.Button(self.canvas, text="✔", fg="green", font=("Arial", 12), height=0, pady=0, padx=0,
                                    width=2, command=lambda: self.createLine(line))
            self.canvas.create_window(event.x + 15, event.y - 25, window=confirm_btn, tags="confirm_btn")

    def canselPoint(self, line):
        if self.canvas.find_withtag('confirm_btn'):
            self.canvas.delete("confirm_btn", 'new_line_1')
            line.points[1] = [np.inf, np.inf]
            for widget in self.sub_menu.winfo_children():
                if isinstance(widget, ttk.OptionMenu):
                    widget['state'] = 'normal'
                elif widget.winfo_name() in ['x1_i', 'y1_i']:
                    widget['state'] = 'normal'
                    widget.delete(0, 'end')
                elif widget.winfo_name() == 'accept':
                    widget['state'] = 'normal'
        elif self.canvas.find_withtag('new_line_0'):
            self.canvas.delete('new_line_0')
            line.points[0] = [np.inf, np.inf]
            for widget in self.sub_menu.winfo_children():
                if widget.winfo_name() in ['x0_i', 'y0_i']:
                    widget['state'] = 'normal'
                    widget.delete(0, 'end')




class ObjectMovementHandler:
    def __init__(self, canvas):
        self.canvas_slave = canvas
        self.start = np.array([0, 0])

        self.canvas_slave.canvas.bind("<Button-2>", self.MMB_press)
        self.canvas_slave.canvas.bind("<B2-Motion>", self.MMB_drag)

    def MMB_press(self, event):
        self.start[:] = [event.x, event.y]

    def MMB_drag(self, event):
        current = np.array([event.x, event.y])
        delta = current - self.start
        self.canvas_slave.center += delta
        for element_id in self.canvas_slave.canvas.find_all():
            self.canvas_slave.canvas.move(element_id, *delta.flatten())
        self.start = current


class BottomBarManager(tk.Frame):
    def __init__(self, root, workspace):
        super().__init__(root, name='bottombar')
        self.workspace_slave = workspace
        self.labels = {'thickness': tk.Label(self, text='Base thickness: 1.0'),
                       'coordinates': tk.Label(self, text='')}

        self.scales = {'thickness': tk.Scale(self, orient=tk.HORIZONTAL,
                                             from_=WorkSpaceManager.BASE_THICKNESS_SCOPE[0],
                                             to=WorkSpaceManager.BASE_THICKNESS_SCOPE[1],
                                             command=self.updateThickness, resolution=0.05, showvalue=False)}
        self.scales['thickness'].set(1.0)

        for i in range(2, 8):
            self.columnconfigure(i, weight=1)

        self.labels['thickness'].grid(row=0, column=0, sticky='nse', padx=(5, 2))
        self.scales['thickness'].grid(row=0, column=1, sticky='nsew', pady=10)
        self.labels['coordinates'].grid(row=0, column=8, sticky='nse', padx=(0, 5))

        self.workspace_slave.canvas.bind('<Motion>', self.setCurrentMouseCoords)

    def setCurrentMouseCoords(self, event):
        self.labels['coordinates']['text'] = 'X={}; Y={}'.format(event.x - self.workspace_slave.center[0],
                                                                 self.workspace_slave.center[1] - event.y)

    def updateThickness(self, value):
        self.workspace_slave.updateThickness(float(value))
        self.labels['thickness']['text'] = 'Base thickness: ' + value


class Line:
    def __init__(self, type_=None):
        self.points = np.full((2, 2), np.Inf)
        self.type = type_


if __name__ == '__main__':
    app = Application()
    app.mainloop()
