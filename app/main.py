from nicegui import ui, app
from app.api.auth import router as auth_router

app.add_static_files(
    '/assets',
    'app/ui/assets'
)

app.include_router(auth_router)

ui.add_head_html("""
<link rel="stylesheet" href="/assets/css/main.css">
""", shared=True)

ui.add_body_html("""
<script src="/assets/js/main.js"></script>
""", shared=True)

import app.ui.pages.dashboard
import app.ui.pages.login
import app.ui.pages.signup
import app.ui.pages.dashboard
import app.ui.pages.profile
import app.ui.pages.tool_page

ui.run(
    title='ToolBox',
    dark=True,
    reload=True
)

