import tkinter as tk
from tkinter import messagebox, ttk
import mysql.connector as mc
import pandas as pd
from datetime import datetime
# --- Safe Session Reset for Spyder ---
if 'con' in globals():
    try:
        if globals()['con'].is_connected():
            globals()['cur'].close()
            globals()['con'].close()
    except Exception:
        pass

# --- Connect to MySQL Database ---
try:   
    con=mc.connect(
        host="localhost",
        user="root",
        password="oursql",
        database="library",
        connection_timeout=2
    )
    cur=con.cursor()
except mc.Error as err:
    print(f"Database Connection Error: {err}")
    exit()

# --- Database Operations ---

def run_add_book(entries,window):
    try:
        bookid=int(entries['id'].get())
        title=entries['title'].get()
        author=entries['author'].get()
        genre=entries['genre'].get()

        if not title or not author or not genre:
            messagebox.showwarning("Input Error","All fields are required!")
            return

        q="INSERT INTO book_details VALUES (%s,%s,%s,%s)"
        cur.execute(q,(bookid,title,author,genre))
        con.commit()

        messagebox.showinfo("Success","Book record added successfully.")
        window.destroy()

    except ValueError:
        messagebox.showerror("Error","Book ID must be an integer.")
    except mc.Error as err:
        messagebox.showerror("Database Error",str(err))


def run_add_member(entries,window):
    try:
        memberid=int(entries['id'].get())
        name=entries['name'].get()
        phone=entries['phone'].get()
        address=entries['address'].get()

        if not name or not phone or not address:
            messagebox.showwarning("Input Error","All fields are required!")
            return

        q="INSERT INTO member_info VALUES (%s,%s,%s,%s)"
        cur.execute(q,(memberid,name,phone,address))
        con.commit()

        messagebox.showinfo("Success","Member record added successfully.")
        window.destroy()

    except ValueError:
        messagebox.showerror("Error","Member ID must be an integer.")
    except mc.Error as err:
        messagebox.showerror("Database Error",str(err))


def run_issue_book(entries,window):
    try:
        issueid=int(entries['issue_id'].get())
        bookid=int(entries['book_id'].get())
        memberid=int(entries['member_id'].get())
        issue_date=entries['date'].get()

        if not issue_date:
            messagebox.showwarning("Input Error","Issue Date is required!")
            return

        try:
            datetime.strptime(issue_date,"%Y-%m-%d")
        except ValueError:
            messagebox.showerror(
                "Invalid Date",
                "Please enter the date in YYYY-MM-DD format."
            )
            return

        # Check if book is already issued
        cur.execute(
            "SELECT * FROM issue_record WHERE bookid=%s",
            (bookid,)
        )

        if cur.fetchone():
            messagebox.showwarning(
                "Unavailable",
                "This book is already issued out!"
            )
            return

        q="INSERT INTO issue_record VALUES (%s,%s,%s,%s)"
        cur.execute(q,(issueid,bookid,memberid,issue_date))
        con.commit()

        messagebox.showinfo("Success","Book issued successfully.")
        window.destroy()

    except ValueError:
        messagebox.showerror("Error","IDs must be integers.")
    except mc.Error as err:
        messagebox.showerror("Database Error",str(err))


def run_return_book(entries,window):
    try:
        bookid=int(entries['book_id'].get())
        return_date=entries['return_date'].get()

        if not return_date:
            messagebox.showwarning(
                "Input Error",
                "Return Date is required!"
            )
            return

        try:
            return_date_obj=datetime.strptime(
                return_date,
                "%Y-%m-%d"
            )
        except ValueError:
            messagebox.showerror(
                "Invalid Date",
                "Please enter the date in YYYY-MM-DD format."
            )
            return

        # Find issue record
        cur.execute(
            "SELECT issuedate FROM issue_record WHERE bookid=%s",
            (bookid,)
        )
        result=cur.fetchone()

        if not result:
            messagebox.showwarning(
                "Not Found",
                f"No active transaction found for Book ID {bookid}."
            )
            return

        issue_date=result[0]

        # Convert database date
        if isinstance(issue_date,str):
            issue_date_obj=datetime.strptime(
                issue_date,
                "%Y-%m-%d"
            )
        else:
            issue_date_obj=datetime.combine(
                issue_date,
                datetime.min.time()
            )

        # Check date
        if return_date_obj<issue_date_obj:
            messagebox.showerror(
                "Invalid Date",
                "Return date cannot be earlier than the issue date."
            )
            return

        # Calculate days used
        days_used=(return_date_obj-issue_date_obj).days

        # Delete issue record
        q="DELETE FROM issue_record WHERE bookid=%s"
        cur.execute(q,(bookid,))
        con.commit()

        if days_used>7:
            messagebox.showwarning(
                "Late Return",
                "Book returned successfully!\n\n"
                "You exceeded the 1-week return deadline.\n"
                "Fine of ₹100 has been issued."
            )
        else:
            messagebox.showinfo(
                "Success",
                "Book returned successfully!\n\n"
                "The book was returned within the 1-week deadline."
            )

        window.destroy()

    except ValueError:
        messagebox.showerror(
            "Error",
            "Book ID must be an integer."
        )
    except mc.Error as err:
        messagebox.showerror(
            "Database Error",
            str(err)
        )


def run_search_member(entry,tree):
    try:
        memberid=int(entry.get())

        q="SELECT * FROM member_info WHERE memberid=%s"
        cur.execute(q,(memberid,))
        data=cur.fetchall()

        for row in tree.get_children():
            tree.delete(row)

        if data:
            df=pd.DataFrame(
                data,
                columns=["Member ID","Name","Phone","Address"]
            )

            for _,row in df.iterrows():
                tree.insert(
                    "",
                    "end",
                    values=list(row)
                )
        else:
            messagebox.showinfo(
                "Not Found",
                "No member found with this ID."
            )

    except ValueError:
        messagebox.showerror(
            "Error",
            "Member ID must be an integer."
        )


# --- Search Available Books ---

def search_books(search_entry,tree):
    search_text=search_entry.get().lower()

    # Clear current display
    for row in tree.get_children():
        tree.delete(row)

    # Select only currently available books
    query="""
    SELECT book_details.*
    FROM book_details
    LEFT JOIN issue_record
    ON book_details.bookid=issue_record.bookid
    WHERE issue_record.bookid IS NULL
    """

    cur.execute(query)
    data=cur.fetchall()

    # Display matching books
    for row in data:
        bookid,title,author,genre=row

        if (
            search_text=="" or
            search_text in str(title).lower() or
            search_text in str(author).lower() or
            search_text in str(genre).lower()
        ):
            tree.insert(
                "",
                "end",
                values=row
            )


# --- GUI Windows ---

def open_add_book_window():
    win=tk.Toplevel(root)
    win.title("Add Book Record")
    win.geometry("350x250")

    fields=['id','title','author','genre']
    labels=['Book ID:','Book Title:','Author Name:','Genre:']
    entries={}

    for i,(field,label) in enumerate(zip(fields,labels)):
        tk.Label(
            win,
            text=label
        ).grid(
            row=i,
            column=0,
            padx=10,
            pady=10,
            sticky="w"
        )

        entry=tk.Entry(win,width=30)
        entry.grid(
            row=i,
            column=1,
            padx=10,
            pady=10
        )

        entries[field]=entry

    tk.Button(
        win,
        text="Submit",
        command=lambda:run_add_book(entries,win),
        bg="#4CAF50",
        fg="white"
    ).grid(
        row=4,
        column=0,
        columnspan=2,
        pady=15
    )


def open_add_member_window():
    win=tk.Toplevel(root)
    win.title("Add Member Record")
    win.geometry("350x250")

    fields=['id','name','phone','address']
    labels=['Member ID:','Full Name:','Phone Number:','Address:']
    entries={}

    for i,(field,label) in enumerate(zip(fields,labels)):
        tk.Label(
            win,
            text=label
        ).grid(
            row=i,
            column=0,
            padx=10,
            pady=10,
            sticky="w"
        )

        entry=tk.Entry(win,width=30)
        entry.grid(
            row=i,
            column=1,
            padx=10,
            pady=10
        )

        entries[field]=entry

    tk.Button(
        win,
        text="Register Member",
        command=lambda:run_add_member(entries,win),
        bg="#4CAF50",
        fg="white"
    ).grid(
        row=4,
        column=0,
        columnspan=2,
        pady=15
    )


def open_issue_book_window():
    win=tk.Toplevel(root)
    win.title("Issue a Book")
    win.geometry("400x310")

    fields=['issue_id','book_id','member_id','date']
    labels=[
        'Issue ID:',
        'Book ID:',
        'Member ID:',
        'Date (YYYY-MM-DD):'
    ]

    entries={}

    for i,(field,label) in enumerate(zip(fields,labels)):
        tk.Label(
            win,
            text=label
        ).grid(
            row=i,
            column=0,
            padx=10,
            pady=10,
            sticky="w"
        )

        entry=tk.Entry(win,width=30)
        entry.grid(
            row=i,
            column=1,
            padx=10,
            pady=10
        )

        entries[field]=entry

    tk.Button(
        win,
        text="Submit",
        command=lambda:run_issue_book(entries,win),
        bg="#4CAF50",
        fg="white"
    ).grid(
        row=4,
        column=0,
        columnspan=2,
        pady=15
    )

    tk.Label(
        win,
        text="Note: The deadline for returning a book is 1 week from the issue date.",
        font=("Aptos Display",9),
        fg="#D32F2F",
        wraplength=360
    ).grid(
        row=5,
        column=0,
        columnspan=2,
        padx=10,
        pady=15
    )


def display_books_window():
    win=tk.Toplevel(root)
    win.title("Available Books")
    win.geometry("700x500")

    # Search section
    search_frame=tk.Frame(win)
    search_frame.pack(pady=10)

    tk.Label(
        search_frame,
        text="Search by Title, Author or Genre:"
    ).grid(
        row=0,
        column=0,
        padx=5
    )

    search_entry=tk.Entry(
        search_frame,
        width=35
    )
    search_entry.grid(
        row=0,
        column=1,
        padx=5
    )

    columns=("Book ID","Title","Author","Genre")

    tree=ttk.Treeview(
        win,
        columns=columns,
        show="headings"
    )

    for col in columns:
        tree.heading(col,text=col)
        tree.column(
            col,
            width=160,
            anchor="center"
        )

    tree.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=10
    )

    # Search button
    tk.Button(
        search_frame,
        text="Search",
        command=lambda:search_books(search_entry,tree),
        bg="#2196F3",
        fg="white"
    ).grid(
        row=0,
        column=2,
        padx=5
    )

    # Search automatically while typing
    search_entry.bind(
        "<KeyRelease>",
        lambda event:search_books(search_entry,tree)
    )

    # Show all available books initially
    search_books(search_entry,tree)


def open_return_book_window():
    win=tk.Toplevel(root)
    win.title("Return Book Menu")
    win.geometry("400x200")

    tk.Label(
        win,
        text="Enter Book ID:"
    ).grid(
        row=0,
        column=0,
        padx=10,
        pady=15
    )

    book_entry=tk.Entry(
        win,
        width=25
    )
    book_entry.grid(
        row=0,
        column=1,
        padx=10,
        pady=15
    )

    tk.Label(
        win,
        text="Return Date (YYYY-MM-DD):"
    ).grid(
        row=1,
        column=0,
        padx=10,
        pady=15
    )

    return_entry=tk.Entry(
        win,
        width=25
    )
    return_entry.grid(
        row=1,
        column=1,
        padx=10,
        pady=15
    )

    entries={
        'book_id':book_entry,
        'return_date':return_entry
    }

    tk.Button(
        win,
        text="Confirm Return",
        command=lambda:run_return_book(entries,win),
        bg="#2196F3",
        fg="white"
    ).grid(
        row=2,
        column=0,
        columnspan=2,
        pady=10
    )


def open_search_member_window():
    win=tk.Toplevel(root)
    win.title("Search Member Details")
    win.geometry("550x300")

    top_frame=tk.Frame(win)
    top_frame.pack(pady=10)

    tk.Label(
        top_frame,
        text="Enter Member ID:"
    ).grid(
        row=0,
        column=0,
        padx=5
    )

    entry=tk.Entry(
        top_frame,
        width=15
    )
    entry.grid(
        row=0,
        column=1,
        padx=5
    )

    columns=("Member ID","Name","Phone","Address")

    tree=ttk.Treeview(
        win,
        columns=columns,
        show="headings",
        height=8
    )

    for col in columns:
        tree.heading(col,text=col)
        tree.column(
            col,
            width=130,
            anchor="center"
        )

    tk.Button(
        top_frame,
        text="Search",
        command=lambda:run_search_member(entry,tree),
        bg="#2196F3",
        fg="white"
    ).grid(
        row=0,
        column=2,
        padx=5
    )

    tree.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=10
    )
    


def on_close():
    try:
        cur.close()
        con.close()
    except Exception:
        pass

    root.destroy()


# --- Main App Window ---

root=tk.Tk()
root.title("Library Management System")
root.geometry("900x600")
root.configure(bg="#D7FFDF")

title=tk.Label(
    root,
    text="📚 Library Management System 📚",
    font=("Georgia",28,"bold"),
    bg="#F1FFE7",
    fg="#4F5D75"
)
title.pack(pady=20)

menu_frame=tk.Frame(
    root,
    bg="white",
    bd=4,
    relief="ridge"
)
menu_frame.pack(pady=20)

buttons = [
    ("📘  Add Book", open_add_book_window, "#4CAF50"),
    ("👤  Add Member", open_add_member_window, "#2196F3"),
    ("📖  Issue Book", open_issue_book_window, "#FF9800"),
    ("📚  Available Books", display_books_window, "#9C27B0"),
    ("↩️  Return Book", open_return_book_window, "#009688"),
    ("🔍  Search Member", open_search_member_window, "#607D8B")
]

for index,(text,command,color) in enumerate(buttons):
    row=index//2
    col=index%2

    btn = tk.Button(
        menu_frame,
        text=text,
        command=command,
        width=24,
        height=2,
        bg=color,
        font=("Aptos Display", 15),
        cursor="hand2",
        relief="raised"
    )

    btn.bind("<Enter>", lambda e, b=btn: b.config(relief="ridge"))
    btn.bind("<Leave>", lambda e, b=btn: b.config(relief="raised"))

    btn.grid(
        row=row,
        column=col,
        padx=8,
        pady=8
    )

exit_btn=tk.Button(
    root,
    text="7. Exit System",
    command=on_close,
    width=48,
    height=2,
    bg="#FF101F",
    fg="#F5F4ED",
    font=("Agency FB",20,"bold"),
    relief="raised",
    cursor="hand2"
)
exit_btn.pack(pady=15)

root.protocol("WM_DELETE_WINDOW",on_close)
root.mainloop()

    

