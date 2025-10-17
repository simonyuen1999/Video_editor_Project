# 🌏 Geographic Translation Editor

A powerful Python GUI application for editing Chinese translations in geographic location CSV files, featuring automated translation suggestions and user-friendly editing interface.

## ✨ Features

### 🔍 **Auto-Search Functionality**
- **Comprehensive Fallback Database**: 100+ major cities worldwide with accurate Chinese translations
- **Smart City Matching**: Handles exact matches, case-insensitive searches, and name variations
- **Reliable Translation System**: Local database eliminates Google search dependencies and anti-bot issues
- **Real-time Suggestions**: Automatically suggests translations when opening entries with missing or incorrect Chinese names
- **User Confirmation**: Smart prompts when suggesting replacements for existing translations
- **Name Variations Support**: Handles prefixes (New, San, Los), suffixes (City), and alternate spellings (St./Saint)

### 📊 **Advanced Data Management**
- **CSV File Support**: Load and edit geo_chinese_bkup.list and other CSV location files
- **Smart Country Filtering**: Filter by specific countries with intelligent sorting behavior
- **Conditional Sorting**: 
  - "All Countries" view: Maintains original data order
  - Specific country view: Alphabetically sorts cities for easy navigation
- **Real-time Updates**: Changes appear immediately in the table view
- **Automatic Backup**: Creates backup files before saving changes

### 🎨 **User-Friendly Interface**
- **Resizable Windows**: Main window (1200x700 minimum) and edit dialogs (400x250 minimum)
- **Responsive Layout**: Form fields expand when window is resized
- **Progress Indicators**: Visual feedback during translation searches
- **Status Messages**: Clear indication of search results and errors

### 🌐 **Multi-Language Support**
- **Bilingual Display**: Shows both English and Chinese names
- **Asian Focus**: Optimized for Asian countries and cities
- **Unicode Support**: Full Chinese character support

## 🚀 Quick Start

### **Installation**

1. **Ensure Python 3.8+ is installed**
2. **Install optional dependencies** (for web search functionality):
   ```bash
   pip install -r geo_editor_requirements.txt
   ```
3. **Run the application**:
   ```bash
   python3 geo_translation_editor.py
   ```

### **Basic Usage**

1. **Load CSV File**: The application auto-loads `geo_chinese_bkup.list` or use "Load CSV File" button
2. **Filter by Country**: Select specific Asian countries from the dropdown
3. **Edit Translations**: Double-click any row to open the edit dialog
4. **Auto-Search**: Click "🔍 Auto Search" or wait for automatic suggestions
5. **Save Changes**: Click "Save Changes" to update the original file

## 🎯 Editing Workflow

### **For Asian Country Translations**

1. **Filter by Country**: 
   ```
   Select "China", "Japan", "Korea", "Thailand", etc. from dropdown
   ```

2. **Identify Issues**:
   - Empty City_zh fields
   - Incorrect machine translations
   - English names in Chinese fields

3. **Use Auto-Search**:
   - Edit dialog automatically searches when City_zh is empty
   - Manual search available via "🔍 Auto Search" button
   - Fallback database provides instant results for common cities

4. **Review and Confirm**:
   - Accept suggested translations
   - Manually edit if needed
   - Save changes when satisfied

## 📋 **Common City Translations Included**

### **China**
- Beijing → 北京
- Shanghai → 上海
- Guangzhou → 广州
- Shenzhen → 深圳

### **Japan**
- Tokyo → 东京
- Osaka → 大阪
- Kyoto → 京都
- Yokohama → 横滨

### **Korea**
- Seoul → 首尔
- Busan → 釜山
- Incheon → 仁川

### **Southeast Asia**
- Bangkok → 曼谷
- Kuala Lumpur → 吉隆坡
- Singapore → 新加坡
- Jakarta → 雅加达

## 🛠️ Technical Features

### **Robust Error Handling**
- Graceful fallback when web search fails
- Works without internet connection using fallback database
- Clear error messages and status updates

### **Performance Optimizations**
- Background threading for web searches
- Efficient CSV parsing and updating
- Responsive UI during long operations

### **Data Safety**
- Automatic backup creation before saving
- Original file structure preservation
- Undo-friendly workflow

## 🔧 Troubleshooting

### **Common Issues**

1. **tkinter not available**:
   ```bash
   # macOS with Homebrew
   brew install python-tk
   
   # Ubuntu/Debian
   sudo apt-get install python3-tk
   ```

2. **Web search not working**:
   - Install requests: `pip install requests`
   - Application will use fallback translations without requests

3. **File loading errors**:
   - Ensure CSV file has proper headers
   - Check file encoding (should be UTF-8)

### **System Requirements**
- Python 3.8+
- tkinter (usually included with Python)
- Optional: requests library for web search

## 📄 File Format Support

### **Input CSV Format**
```csv
City_en,City_zn,Region_en,Region_zn,Subregion_en,Subregion_zn,CountryCode,Country_en,Country_zn,TimeZone,Latitude,Longitude
Tokyo,东京,Tokyo Metropolis,东京都,...
```

### **Supported Variations**
- `City_en` / `city_en` / `City`
- `City_zn` / `city_zh` / `City_zh`
- Flexible delimiter detection (comma or tab)

## 🤝 Contributing

This tool is designed for vacation media organization projects. Feel free to:
- Add more city translations to the fallback database
- Improve translation search algorithms
- Enhance the user interface
- Add support for additional languages

## 📝 License

Open source - feel free to use and modify for your geographic data management needs.

---

**Perfect for**: Vacation media organizers, geographic data managers, international travel applications, and anyone working with bilingual location databases.