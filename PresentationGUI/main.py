import page

def main():
    app = page.trafficApp()
    app.wm_title("Traffic Monitor")
    app.wm_geometry("1200x800")
    app.mainloop()

main()