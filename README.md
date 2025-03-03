# BMC-API-APP
Python GUI to create API requests to BMC AMI OPs Console
    def merge_configurations(self, username, source_hostname, target_hostname):
        def clear_directory(directory):
            for root, dirs, files in os.walk(directory, topdown=False):
                for name in files:
                    file_path = os.path.join(root, name)
                    try:
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
            # Define OneDrive Documents path
            onedrive_docs = os.path.join(os.path.expanduser('~'), "OneDrive - Fiserv Corp", "Documents")
            
            # Create temporary directory structure within OneDrive Documents
            with tempfile.TemporaryDirectory(dir=onedrive_docs) as temp_dir:
                # Define temporary working directories
                merge_base_dir = os.path.join(temp_dir, "MergedSaveConfig")
                source_extract_dir = os.path.join(merge_base_dir, "sourceExtracted")
                target_extract_dir = os.path.join(merge_base_dir, "targetExtracted")
                merge_file_dir = os.path.join(merge_base_dir, "mergeFile")
                
                # Create temporary directories
                for dir_path in [merge_base_dir, source_extract_dir, target_extract_dir, merge_file_dir]:
                    os.makedirs(dir_path)
                    print(f"Created temporary directory: {dir_path}")

                # Define source and target zip paths in OneDrive Documents
                source_zip = os.path.join(onedrive_docs, "source_Merge.zip")
                target_zip = os.path.join(onedrive_docs, "target_Merge.zip")

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
                from datetime import datetime
                current_date = datetime.now().strftime("%d%b%Y").upper()
                version = "4.1.05"
                source_server = source_hostname.split('.')[0].upper()
                target_server = target_hostname.split('.')[0].upper()
                merged_zip_name = f"{source_server}_{target_server}_Merged_V{version}_{current_date}"

                # Update descriptor.xml
                descriptor_path = os.path.join(merge_file_dir, "descriptor.xml")
                if os.path.exists(descriptor_path):
                    print("\nUpdating descriptor.xml...")
                    
                    import xml.etree.ElementTree as ET
                    tree = ET.parse(descriptor_path)
                    root = tree.getroot()
                    
                    name_element = root.find('name')
                    if name_element is not None:
                        name_element.text = f"{source_server}_{target_server}_Merged_V{version}_{current_date}"
                        print(f"Updated name in descriptor.xml to: {name_element.text}")

                    description_element = root.find('description')
                    if description_element is not None:
                        description_element.text = f"Config from {source_server} brought to {target_server} on {current_date}"
                        print(f"Updated description in descriptor.xml to: {description_element.text}")

                    # Format and save the XML
                    import xml.dom.minidom
                    xml_str = ET.tostring(root, encoding='utf-8')
                    dom = xml.dom.minidom.parseString(xml_str)
                    pretty_xml = dom.toprettyxml(indent="    ")
                    with open(descriptor_path, 'w', encoding='utf-8') as f:
                        f.write(pretty_xml)
                else:
                    print("Warning: descriptor.xml not found in merge directory")

                # Create the merged zip file
                os.chdir(merge_file_dir)
                merged_zip_path = os.path.join(onedrive_docs, f"c{merged_zip_name}.zip")
                shutil.make_archive(os.path.join(onedrive_docs, f"c{merged_zip_name}"), 'zip', '.')

                print(f"\nMerged zip file created:")
                print(f"- File Location: {merged_zip_path}")
                print(f"- Size: {os.path.getsize(merged_zip_path)} bytes")

                return merged_zip_path

        except Exception as e:
            print(f"Error during merge: {str(e)}")
            raise