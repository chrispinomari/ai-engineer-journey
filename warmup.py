def total_by_category(records):
    totals = {}
    for record in records:
        category = record["category"]
        totals[category] = totals.get(category, 0) + record["amount"]
    return totals

def most_expensive_item(records):
    return max(records, key=lambda record: record["amount"])

print(total_by_category(expenses))
top = most_expensive_item(expenses)
print("Most expensive:", top["item"], top["amount"])