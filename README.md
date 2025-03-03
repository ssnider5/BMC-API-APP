import os
import zipfile
import shutil
import tempfile
from datetime import datetime
import xml.etree.ElementTree as ET
import xml.dom.minidom

def merge_configurations(self, username, source_hostname, target_hostname):
    def clear_directory(directory):
        # Walk the directory tree from the bottom up
        for root, dirs, files in os.walk(directory, topdown=False):
            for name in files:
                file_path = os.path.join(root, name)
                try:
                    # Ensure the file is writable
                    os.chmod(file_path, 0o777)
                    os.remove(file_path)
                except Exception as e:
                    print(f"Could not delete file {file_path}: {e}")
            for name in dirs:
                dir_path = os.path.join(root, name)
                try:
                    os.chmod(dir_path, 0o777)
                    os.rmdir(dir_path)
                except Exception as e:
                    print(f"Could not delete directory {dir_path}: {e}")

    try:
        # Use the current working directory as the base directory
        base_dir = os.getcwd()
        merge_base_dir = os.path.join(base_dir, "MergedSaveConfig")
        source_extract_dir = os.path.join(merge_base_dir, "sourceExtracted")
        target_extract_dir = os.path.join(merge_base_dir, "targetExtracted")
        merge_file_dir = os.path.join(merge_base_dir, "mergeFile")
        
        # Create directories if they don't exist
        for dir_path in [merge_base_dir, source_extract_dir, target_extract_dir, merge_file_dir]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                print(f"Created directory: {dir_path}")

        # Optionally clear the directories without admin rights
        for dir_path in [source_extract_dir, target_extract_dir, merge_file_dir]:
            if os.path.exists(dir_path):
                clear_directory(dir_path)  # use the helper function defined above

        # Define source and target zip paths within the base directory
        source_zip = os.path.join(merge_base_dir, "source_Merge.zip")
        target_zip = os.path.join(merge_base_dir, "target_Merge.zip")

        print(f"\nSource zip size: {os.path.getsize(source_zip)} bytes")
        print(f"Target zip size: {os.path.getsize(target_zip)} bytes")

        print("\nExtracting source zip...")
        with zipfile.ZipFile(source_zip, 'r') as zip_ref:
            zip_ref.extractall(source_extract_dir)

        print("\nExtracting target zip...")
        with zipfile.ZipFile(target_zip, 'r') as zip_ref:
            zip_ref.extractall(target_extract_dir)

        print("\nCopying all files from source...")
        for item in os.listdir(source_extract_dir):
            s = os.path.join(source_extract_dir, item)
            d = os.path.join(merge_file_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

        print("\nDeleting directories from merge that will be replaced:")
        directories_to_replace = ['licensemanager', 'tomcat', 'security']
        for directory in directories_to_replace:
            merged_dir_path = os.path.join(merge_file_dir, directory)
            if os.path.exists(merged_dir_path):
                print(f"- Deleting /{directory}")
                shutil.rmtree(merged_dir_path)

        print("\nCopying directories from target:")
        for directory in directories_to_replace:
            target_dir_path = os.path.join(target_extract_dir, directory)
            merged_dir_path = os.path.join(merge_file_dir, directory)
            if os.path.exists(target_dir_path):
                print(f"- Copying /{directory}")
                shutil.copytree(target_dir_path, merged_dir_path)

        # Create merged zip file with specific naming convention
        current_date = datetime.now().strftime("%d%b%Y").upper()
        version = "4.1.05"
        source_server = source_hostname.split('.')[0].upper()
        target_server = target_hostname.split('.')[0].upper()
        merged_zip_name = f"{source_server}_{target_server}_Merged_V{version}_{current_date}"

        # Update descriptor.xml if it exists
        descriptor_path = os.path.join(merge_file_dir, "descriptor.xml")
        if os.path.exists(descriptor_path):
            print("\nUpdating descriptor.xml...")
            # Read the current content
            with open(descriptor_path, 'r') as file:
                content = file.read()
            
            # Parse XML
            root = ET.fromstring(content)
            
            # Update the name field
            name_element = root.find('name')
            if name_element is not None:
                name_element.text = f"{source_server}_{target_server}_Merged_V{version}_{current_date}"
                print(f"Updated name in descriptor.xml to: {name_element.text}")

            # Update the description field
            description_element = root.find('description')
            if description_element is not None:
                description_element.text = f"Config from {source_server} brought to {target_server} on {current_date}"
                print(f"Updated description in descriptor.xml to: {description_element.text}")

            # Write back the modified XML
            tree = ET.ElementTree(root)
            tree.write(descriptor_path, encoding='utf-8', xml_declaration=True)
            
            # Format the XML file with proper indentation
            with open(descriptor_path, 'r') as file:
                xml_content = file.read()
            dom = xml.dom.minidom.parseString(xml_content)
            pretty_xml = dom.toprettyxml(indent="    ")
            with open(descriptor_path, 'w') as file:
                file.write(pretty_xml)
        else:
            print("Warning: descriptor.xml not found in merge directory")

        merged_zip_path = os.path.join(merge_base_dir, merged_zip_name)

        # Clean up any existing zip file
        if os.path.exists(f"{merged_zip_path}.zip"):
            os.remove(f"{merged_zip_path}.zip")

        print("\nCreating merged zip file...")
        # Change to the parent directory of mergeFile
        original_dir = os.getcwd()
        os.chdir(merge_base_dir)
        
        # Create the zip file using shutil.make_archive
        shutil.make_archive(merged_zip_path, 'zip', 'mergeFile')
        
        # Change back to the original directory
        os.chdir(original_dir)

        print(f"\nMerged zip contents:")
        with zipfile.ZipFile(f"{merged_zip_path}.zip", 'r') as zip_ref:
            file_list = zip_ref.namelist()
            print(f"Total files: {len(file_list)}")
            print("Key directories:")
            for d in directories_to_replace:
                files = [f for f in file_list if f.startswith(f"{d}/")]
                print(f"- /{d}/: {len(files)} files")

        # Create a copy with a 'c' prefix
        copy_zip_name = f"c{merged_zip_name}.zip"
        copy_zip_path = os.path.join(merge_base_dir, copy_zip_name)
        
        print(f"\nCreating copy of zip file...")
        shutil.copy2(f"{merged_zip_path}.zip", copy_zip_path)
        print(f"Copy created: {copy_zip_path}")

        print(f"\nMerged zip files created:")
        print(f"- Original Location: {merged_zip_path}.zip")
        print(f"- Copy Location: {copy_zip_path}")
        print(f"- Size: {os.path.getsize(f'{merged_zip_path}.zip')} bytes")

        return f"{merged_zip_path}.zip"

    except Exception as e:
        print(f"Error during merge: {str(e)}")
        raise
