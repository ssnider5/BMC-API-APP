Dim shell
Set shell = CreateObject("WScript.Shell")

' 0 = hidden window, 1 = shown normal
shell.Run "cmd /c run_app.bat", 0, True
