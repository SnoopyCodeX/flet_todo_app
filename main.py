import asyncio
from json.decoder import JSONDecodeError, JSONDecoder
from json.encoder import JSONEncoder

import flet
from flet import (
    AlertDialog, 
    Column, 
    CrossAxisAlignment, 
    FloatingActionButton, 
    IconButton,
    ListView,
    MainAxisAlignment,
    OutlinedButton, 
    Page, 
    ProgressBar, 
    Row, 
    ScrollMode, 
    Tab,
    Tabs, 
    Text, 
    TextButton, 
    TextField, 
    TextThemeStyle, 
    ThemeMode,
    UserControl, 
    icons,
)

from components.task_item import Task


class TodoApp(UserControl):
    def __init__(self, page: Page, update_theme):
        super().__init__()
        
        self.page = page
        self.tasks = Column()
        
        self.completed_tasks_count = 0
        self.update_theme = update_theme
        self.theme = 'light'
        
        asyncio.run_coroutine_threadsafe(self.get_saved_theme(), asyncio.get_running_loop())
        asyncio.run_coroutine_threadsafe(self.get_tasks_locally(), asyncio.get_running_loop())
        
        self.new_task = TextField(
            hint_text="What needs to be done?", 
            border_color='blue', 
            prefix_icon=icons.ADD_TASK_OUTLINED,
            expand=True, 
            on_submit=self.add_clicked,
        )
        self.items_left = Text("0 tasks left")
        
        self.filter = Tabs(
            selected_index=0,
            on_change=self.tabs_changed,
            tabs=[
                Tab(text="All", icon=icons.LIST_OUTLINED),
                Tab(text="Not Done", icon=icons.CANCEL_OUTLINED),
                Tab(text="Done", icon=icons.TASK_ALT_OUTLINED),
            ],
        )
        
        self.progress = ProgressBar(
            value=0,
            bar_height=6,
            expand=True,
        )
        
        self.theme_button = IconButton(
            icon=icons.WB_SUNNY_OUTLINED if self.theme == 'dark' else icons.DARK_MODE_OUTLINED,
            tooltip="Change theme",
            on_click=self.change_theme,
        )
    
    def build(self):
        self.main_view = Column(
            width=600,
            controls=[
                Row(
                    alignment=MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        Text(
                            value="TODO App using Flet",
                            style=TextThemeStyle.HEADLINE_MEDIUM,
                        ),
                        Row(
                            spacing=10,
                            controls=[
                                self.theme_button,
                                IconButton(
                                    icon=icons.CODE_OUTLINED,
                                    tooltip="Source code",
                                    on_click=self.open_repository,
                                ),
                            ],
                        ),
                    ],
                ),
                Row(
                    controls=[
                        self.new_task,
                        FloatingActionButton(icon=icons.ADD, on_click=self.add_clicked)
                    ],
                ),
                Column(
                    spacing=25,
                    controls=[
                        Row(
                            controls=[
                                Text(value="0%"),
                                self.progress,
                                Text(value="100%"),
                            ],
                        ),
                        self.filter,
                        self.tasks,
                        Row(
                            alignment=MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=CrossAxisAlignment.CENTER,
                            controls=[
                                self.items_left,
                                OutlinedButton(
                                    text="Clear done tasks",
                                    on_click=lambda _: asyncio.run_coroutine_threadsafe(
                                        self.show_dialog_message(
                                            title="Please confirm",
                                            message="Do you really want to clear all done tasks?",
                                            action_confirm=self.clear_clicked,
                                            close_on_tap_outside=False,
                                        ),
                                        asyncio.get_running_loop(),
                                    ) if self.completed_tasks_count > 0 else None,
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )
        
        return self.main_view
        
    async def open_repository(self, _):
        await self.page.launch_url_async("https://github.com/SnoopyCodeX/flet_todo_app")    

    async def change_theme(self, _):
        self.theme = 'light' if self.theme == 'dark' else 'dark'
        
        self.theme_button.icon = icons.WB_SUNNY_OUTLINED if self.theme == 'dark' else icons.DARK_MODE_OUTLINED
        
        await self.update_async(from_update_theme=True)
        await self.update_theme(self.theme)
        await self.page.client_storage.set_async('theme', self.theme)
        
    async def get_saved_theme(self):
        saved_theme = await self.page.client_storage.get_async("theme")
        self.theme = saved_theme if saved_theme != None else 'light'
        
        self.theme_button.icon = icons.WB_SUNNY_OUTLINED if self.theme == 'dark' else icons.DARK_MODE_OUTLINED
        
        await self.update_theme(self.theme)
        
    async def save_tasks_locally(self, value: list | None = None):
        tasks_to_be_saved = value if value != None else self.saved_tasks
        
        for index in range(len(self.tasks.controls)): 
            ui_task: Task = self.tasks.controls[index]
            
            tasks_to_be_saved[index]['id'] = ui_task.id
            tasks_to_be_saved[index]['task_name'] = ui_task.task_name
            tasks_to_be_saved[index]['is_done'] = ui_task.completed
        
        await self.page.client_storage.set_async("tasks", JSONEncoder().encode(tasks_to_be_saved))
        
    async def get_tasks_locally(self):
        try:
            jsonTasks = await self.page.client_storage.get_async("tasks")
        
            # If local storage is empty, create an empty saved_tasks
            if not jsonTasks:
                self.saved_tasks = []
                await self.update_async()
                return
            
            self.saved_tasks = JSONDecoder().decode(jsonTasks)
            self.tasks.controls = [Task(task['id'], task['task_name'], self.task_delete, self.task_status_changed, self.task_name_change, self.show_dialog_message, task['is_done']) for task in self.saved_tasks]
            await self.update_async(from_initial_get=True)
        except JSONDecodeError:
            self.saved_tasks = []
            await self.update_async()
        
    async def add_clicked(self, _):
        # Do nothing if task name is empty
        if(not self.new_task.value.strip()):
            self.new_task.value = ""
            await self.new_task.focus_async()
            await self.update_async()
            return
        
        id = len(self.saved_tasks) + 1
        task = Task(id, self.new_task.value.strip(), self.task_delete, self.task_status_changed, self.task_name_change, self.show_dialog_message)
        self.tasks.controls.append(task)
        self.new_task.value = ""
        
        self.saved_tasks.append({"id": id, "task_name": task.task_name, "is_done": False})
        
        await self.new_task.focus_async()
        await self.update_async()
        
    async def task_status_changed(self, _):
        await self.update_async()
        
    async def task_name_change(self, _):
        await self.update_async()
         
    async def task_delete(self, task: Task):
        if self.page.dialog.open:
            self.page.dialog.open = False
            await self.page.update_async()
        
        self.tasks.controls.remove(task)
        
        for savedTask in self.saved_tasks:
            if savedTask['id'] == task.id:
                self.saved_tasks.remove(savedTask)
                
        await self.update_async() 
    
    async def tabs_changed(self, _):
        await self.update_async(tab_update=True)
        
    async def clear_clicked(self, _):
        self.page.dialog.open = False
        await self.page.update_async()
        
        for task in self.tasks.controls[:]:
            if task.completed:
                await self.task_delete(task)
        
    async def update_async(self, tab_update=False, from_initial_get=False, from_update_theme=False):
        # Get selected tab
        status = self.filter.tabs[self.filter.selected_index].text
        
        self.completed_tasks_count = 0
        not_completed_tasks_count = 0
        
        # Filter tasks based on current tab selection
        for task in self.tasks.controls:
            task.visible = (
                status == "All" or 
                (status == "Done" and task.completed) or 
                (status == "Not Done" and not task.completed)
            )
            
            # Count tasks that are not yet completed and completed
            if not task.completed:
                not_completed_tasks_count += 1
            else:
                self.completed_tasks_count += 1
                
        # Don't trigger saving to local storage if the update
        # was called on tab change or inside of @self.get_tasks_locally or inside of @self.change_theme
        if not tab_update and not from_initial_get and not from_update_theme:
            await self.save_tasks_locally()
        
        progress = (self.completed_tasks_count / len(self.saved_tasks)) * 100 if len(self.saved_tasks) > 0 else 0.0
        text_progress = "{0:.2f}%".format(progress) if not progress.is_integer() else "{0:.0f}%".format(progress)
        
        # Update progress text
        self.main_view.controls[2].controls[0].controls[0].value = text_progress
        
        # Update progress bar
        self.progress.value = progress / 100
        
        # Update progress bar color based on current progress
        if progress < 30:
            self.progress.color = 'red'
        elif progress >= 30 and progress < 50:
            self.progress.color = 'yellow'
        elif progress >= 50 and progress < 80:
            self.progress.color = 'amber'
        elif progress >= 80 and progress < 100:
            self.progress.color = 'orange'
        else:
            self.progress.color = 'green'
            
        # Enable/Disable 'Clear done tasks' button
        self.main_view.controls[2].controls[3].controls[1].disabled = self.completed_tasks_count == 0
        
        # Update active task counter
        self.items_left.value = f"{not_completed_tasks_count} active task{'s' if not_completed_tasks_count > 1 or not_completed_tasks_count == 0 else ''} left"
        await super().update_async()
        
    async def show_dialog_message(self, title: str, message: str, action_confirm=None, action_cancel = None, confirm_button_text="Yes", cancel_button_text="No", close_on_tap_outside=True):
        async def close_dialog(_):
            dialog.open = False
            await self.page.update_async()
        
        dialog = AlertDialog(
            title=Text(title),
            content=Text(message),
            modal=close_on_tap_outside,
            actions=[
                TextButton(cancel_button_text, on_click=action_cancel if action_cancel != None else close_dialog),
                TextButton(confirm_button_text, on_click=action_confirm if action_confirm != None else close_dialog),
            ],
            actions_alignment=MainAxisAlignment.END
        )
        
        self.page.dialog = dialog
        dialog.open = True
        await self.page.update_async()
        
async def main(page: Page):
    page.title = "To-Do App"
    page.horizontal_alignment = CrossAxisAlignment.CENTER
    page.scroll = ScrollMode.ADAPTIVE
    page.theme_mode = ThemeMode.LIGHT
    page.theme = flet.Theme(use_material3=True)
    await page.update_async()
    
    async def update_theme(theme: str):
        page.theme_mode = ThemeMode.LIGHT if theme == 'light' else ThemeMode.DARK
        await page.update_async()
    
    app = TodoApp(page=page, update_theme=update_theme)
    await page.add_async(app)
    
flet.app(main)
    