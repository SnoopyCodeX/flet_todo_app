import asyncio

from flet import (
    Checkbox, 
    Column, 
    IconButton, 
    Row, 
    Text, 
    TextDecoration,
    TextDecorationStyle, 
    TextField, 
    TextSpan, 
    TextStyle,
    UserControl, 
    colors, 
    icons,
)


class Task(UserControl):
    def __init__(self, id, task_name, task_delete, task_status_change, task_name_change, show_dialog_message, completed=False):
        super().__init__()
        self.id = id
        self.completed = completed
        self.task_status_change = task_status_change
        self.task_name_change = task_name_change
        self.show_dialog_message = show_dialog_message
        self.task_name = task_name
        self.task_delete = task_delete
        
    def build(self):
        self.display_task = Checkbox(
            value=False, 
            label=self.task_name, 
            on_change=self.status_changed,
        ) if not self.completed else Row(
            controls=[
                Checkbox(
                    value=True,
                    on_change=self.status_changed,
                ),
                Text(
                    spans=[
                        TextSpan(
                            text=self.task_name,
                            style=TextStyle(
                                decoration=TextDecoration.LINE_THROUGH,
                                decoration_style=TextDecorationStyle.WAVY,
                                decoration_thickness=3,
                                decoration_color='red',
                                italic=True,
                            ),
                        ),
                    ],
                ),
            ],
        )
        self.edit_name = TextField(expand=1, on_submit=self.save_clicked)
        
        self.display_view = Row(
            alignment="spaceBetween",
            vertical_alignment="center",
            controls=[
                self.display_task,
                Row(
                    spacing=0,
                    controls=[
                        IconButton(
                            icon=icons.CREATE_OUTLINED,
                            tooltip="Edit task",
                            on_click=self.edit_clicked,
                        ),
                        IconButton(
                            icon=icons.DELETE_OUTLINE,
                            tooltip="Delete task",
                            on_click=lambda _: asyncio.run_coroutine_threadsafe(
                                self.show_dialog_message(
                                    title="Please confirm",
                                    message="Do you really want to delete this task?",
                                    action_confirm=self.delete_clicked,
                                    close_on_tap_outside=False,
                                ),
                                asyncio.get_running_loop(),
                            ),
                        ),
                    ],
                ),
            ],
        )
        
        self.edit_view = Row(
            visible=False,
            alignment="spaceBetween",
            vertical_alignment="center",
            controls=[
                self.edit_name,
                IconButton(
                    icon=icons.DONE_OUTLINE_OUTLINED,
                    icon_color=colors.GREEN,
                    tooltip="Update task",
                    on_click=self.save_clicked,
                ),
            ],
        )
        
        return Column(controls=[
            self.display_view,
            self.edit_view,
        ])
        
    async def status_changed(self, _):
        self.completed = not self.completed
        
        self.display_task = Checkbox(
            value=False, 
            label=self.task_name, 
            on_change=self.status_changed,
        ) if not self.completed else Row(
            controls=[
                Checkbox(
                    value=True,
                    on_change=self.status_changed,
                ),
                Text(
                    spans=[
                        TextSpan(
                            text=self.task_name,
                            style=TextStyle(
                                decoration=TextDecoration.LINE_THROUGH,
                                decoration_style=TextDecorationStyle.WAVY,
                                decoration_thickness=3,
                                decoration_color='red',
                                italic=True,
                            ),
                        ),
                    ],
                ),
            ],
        )
        
        self.display_view.controls[0] = self.display_task
        
        await self.task_status_change(self)
        await self.update_async()
        
    async def edit_clicked(self, _):
        self.edit_name.value = self.task_name
        self.display_view.visible = False
        self.edit_view.visible = True
        await self.update_async()
        
    async def save_clicked(self, _):
        # Do nothing if the new task name is empty
        if not self.edit_name.value.strip():
            self.edit_name.value = self.task_name
            self.display_view.visible = False
            self.edit_view.visible = True
            await self.update_async()
            return
        
        # Do nothing if the new task name is the same as the old task name
        if self.edit_name.value.strip() == self.task_name:
            self.edit_name.value = self.task_name
            self.display_view.visible = True
            self.edit_view.visible = False
            await self.update_async()
            return
        
        self.task_name = self.edit_name.value.strip()
        
        if not self.completed:
            self.display_task.label = self.edit_name.value.strip()
        else:
            self.display_task.controls[1].spans[0].text = self.edit_name.value.strip()
            
        self.display_view.visible = True
        self.edit_view.visible = False
        await self.task_name_change(self)
        await self.update_async()
        
    async def delete_clicked(self, _):
        await self.task_delete(self)