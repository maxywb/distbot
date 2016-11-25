from collections import namedtuple

Command= namedtuple("Command", ["args","command"])

def find_string_end(query):
    i = 0
    pieces = list()
    while len(query) > 0:
        part = query[i]
        pieces.append(part)
        del query[i]
        if part[-1] == "\"":
            i += 1
            break

    return " ".join(pieces), query

def tokenize(input):
    if isinstance(input, list):
        query = input
    else:
        query = input.split()

    while "=" in query:
        equals = query.index("=")
        start = equals - 1
        end = equals + 1
        
        query[start] = "%s=%s" % (query[start], query[end])
        del query[equals:end+1]

    args = dict()
    i = 0
    while i < len(query):
        if query[i].startswith("!"):
            parts = query[i].split("=")
            key = parts[0][1:]
            value = "=".join(parts[1:])
            
            if len(value) <= 0:
                i += 1
                continue

            if value[0] == "\"":
                remainder, new_query = find_string_end(query[i+1:])
                value += " " + remainder
                value = value.replace("\"", "")
                del query[i+1:]
                query += new_query

            args[key] = value
            del query[i]
            continue
        elif query[i][0] == "\"":
            base = query[i]
            remainder, new_query = find_string_end(query[i+1:])
            value = query[i] + " " + remainder
            query[i] = value.replace("\"", "")
            del query[i+1:]
            query += new_query
                
        i += 1

    return Command(args, query)
