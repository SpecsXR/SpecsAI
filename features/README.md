# Features

প্রতিটি ফিচার **আলাদা ফাইলে** রাখা হয়েছে।

## বর্তমান ফিচার

| ফাইল | বর্ণনা |
|------|--------|
| `mouse_follow.py` | মাউস অনুসরণ – মাথা/চোখ ঘোরে |
| `zoom.py` | হুইল দিয়ে zoom in/out |
| `drag_window.py` | উইন্ডো ড্র্যাগ – মাউস ধরে টেনে মনি্টরের যেকোনো জায়গায় নেওয়া |

## নতুন ফিচার যোগ করা

1. `features/` তলে নতুন ফাইল তৈরি করো, যেমন `features/my_feature.py`।
2. ওখানে ফাংশন/ক্লাস লিখো (যেমন `handle_click(widget, event)`).
3. `ui/live2d_widget.py` তে import করে সেই ফাংশন কল করো (যেমন `mousePressEvent` / `keyPressEvent` ইত্যাদিতে)।

উদাহরণ: `features/drag_window.py` বানাতে চাইলে – ড্র্যাগ লজিক সেই ফাইলে রাখো, তারপর `MainWindow` বা widget এ connect করে দাও।
