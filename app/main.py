from nicegui import ui, app
from app.api.auth import router as auth_router


app.add_static_files(
    '/assets',
    'app/ui/assets'
)
app.include_router(auth_router)

@ui.page('/')
def home():
    ui.label('Hello SandBox')

ui.add_head_html("""
<link rel="stylesheet" href="/assets/css/auth.css">

<script type="module" src="/assets/js/appearance.js"></script>
""", shared=True)


import app.main

import app.ui.pages.login
import app.ui.pages.signup
import app.ui.pages.dashboard
import app.ui.pages.profile
import app.ui.pages.tool_page
import app.ui.pages.forgot_password
import app.ui.pages.reset_password
import app.ui.pages.text_summarizer
import app.ui.pages.json_fixer

# ui.run(
#     title='SandBox',
#     dark=True,
#     reload=True
# )
