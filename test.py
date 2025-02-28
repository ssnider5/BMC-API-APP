class TestZip:
    def test_zip_merge_file(self):
        """Test function to zip contents of mergeFile directory using shutil.make_archive"""
        try:
            # Define the paths
            import os
            import shutil
            from datetime import datetime
            
            # Base directory paths
            user_docs = os.path.join(os.path.expanduser('~'), "OneDrive - Fiserv Corp", "Documents")
            merge_base_dir = os.path.join(user_docs, "MergedSaveConfig")
            merge_file_dir = os.path.join(merge_base_dir, "mergeFile")
            
            # Clean up any existing test zip file
            current_date = datetime.now().strftime("%d%b%Y").upper()
            test_zip_name = f"TEST_MERGE_{current_date}"
            test_zip_path = os.path.join(merge_base_dir, test_zip_name)
            if os.path.exists(f"{test_zip_path}.zip"):
                os.remove(f"{test_zip_path}.zip")
            
            # Verify mergeFile directory exists and has contents
            if not os.path.exists(merge_file_dir):
                raise FileNotFoundError(f"mergeFile directory not found at: {merge_file_dir}")
            
            print(f"\nStarting test zip creation...")
            print(f"Source directory: {merge_file_dir}")
            print(f"Target zip file: {test_zip_path}.zip")
            
            # Change to the parent directory of mergeFile
            original_dir = os.getcwd()
            os.chdir(merge_base_dir)
            
            # Create the zip file using shutil.make_archive
            # Use 'mergeFile' as the base_dir to zip only its contents
            shutil.make_archive(test_zip_path, 'zip', 'mergeFile')
            
            # Change back to original directory
            os.chdir(original_dir)
            
            # Verify zip was created
            if os.path.exists(f"{test_zip_path}.zip"):
                print(f"\nZip file successfully created!")
                print(f"Location: {test_zip_path}.zip")
                print(f"Size: {os.path.getsize(f'{test_zip_path}.zip')} bytes")
                
                # Print contents of zip
                import zipfile
                print("\nZip contents:")
                with zipfile.ZipFile(f"{test_zip_path}.zip", 'r') as zip_ref:
                    file_list = zip_ref.namelist()
                    print(f"Total files: {len(file_list)}")
                    
                    # Print first few files as example
                    print("Sample of files:")
                    for file in file_list[:5]:
                        print(f"- {file}")
                    if len(file_list) > 5:
                        print("...")
                
                return f"{test_zip_path}.zip"
            else:
                raise FileNotFoundError(f"Failed to create zip file at: {test_zip_path}.zip")
                
        except Exception as e:
            print(f"Error during test zip: {str(e)}")
            raise

# Create instance and run test
test = TestZip()
test.test_zip_merge_file()