if __name__ == "__main__":
    try:
        import gui
        gui.main()  
    except Exception as e:
        # Optionally log any errors since we won't have a console
        import logging
        logging.basicConfig(filename='error.log', level=logging.ERROR)
        logging.error(f"Application error: {str(e)}", exc_info=True)