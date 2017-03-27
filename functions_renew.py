#! /usr/bin/env python
# -*- coding: utf-8 -*-


from functions import read_csv, generate_date_range, is_float, is_int


def sprint(text, input_value, *args):
    if not args:
        output = str(format(input_value, '.1f'))
    else:
        output = str(format(input_value, '.1f')) + str(args[0])
    return output


def calculate(i, wind, solar, load, wind_multiplier, solar_multiplier, capacity_storage, wind_price, solar_price, gas_price, price_kwh_storage, discount_rate_storage, years_storage):
    rng = len(wind)
    
    # объ€вление массивов анализируемых данных
    wind = list(wind)
    solar = list(solar)
    load = list(load)
    charged = [0] * rng
    discharged = [0] * rng
    gas = [0] * rng
    overhead = [0] * rng
    inbattery_list = [0] * rng

    inbattery = 0
    overhead_count = 0

    # формирование основного массива результатов

    #print i
    for hour in range(rng):
        wind[hour] = (wind[hour]) * wind_multiplier[i]
        solar[hour] = (solar[hour]) * solar_multiplier[i]

        if load[hour] > wind[hour] + solar[hour]:      # если идёт разрядка
            if load[hour] - wind[hour] - solar[hour] < inbattery:     # если в батарее достаточно ээ, то вычисляем сколько нужно и вычитаем
                discharged[hour] = load[hour] - (wind[hour] + solar[hour])
                inbattery -= discharged[hour]      # вычисляем новый уровень батареи
                inbattery_list[hour] = inbattery

            else:       # если в батарее недостаточно ээ, то
                discharged[hour] = inbattery
                inbattery = 0
                gas[hour] = load[hour] - (wind[hour] + solar[hour]) - discharged[hour]
                inbattery_list[hour] = inbattery

        else:         # идёт зарядка
            if wind[hour] + solar[hour] - load[hour] < capacity_storage[i] - inbattery:     # если в аккуме хватает места
                charged[hour] = wind[hour] + solar[hour] - load[hour]
                inbattery = inbattery + wind[hour] + solar[hour] - load[hour]
                inbattery_list[hour] = inbattery

            else:          # если в аккуме не хватает места
                charged[hour] = capacity_storage[i] - inbattery
                inbattery = capacity_storage[i]
                overhead[hour] = wind[hour] + solar[hour] - load[hour] - charged[hour]
                inbattery_list[hour] = inbattery
                overhead_count += 1

    values = values_func(i, wind, solar, load, charged, discharged, gas, overhead, overhead_count, capacity_storage[i], wind_price, solar_price, gas_price, price_kwh_storage[i], discount_rate_storage, years_storage, wind_multiplier[i], solar_multiplier[i])
    if i == 0:
        return wind, solar, gas, charged, discharged, inbattery_list, capacity_storage, values
    else:
        return values


def calculate_cycle(wind, solar, load, wind_multiplier, solar_multiplier, capacity_storage, wind_price, solar_price, gas_price, price_kwh_storage,
                    discount_rate_storage, years_storage):

    wind_capacity = 102.5 * wind_multiplier
    solar_capacity = 55 * solar_multiplier

    rng = len(wind)

    wind = list(wind)
    solar = list(solar)
    load = list(load)
    charged = [0] * rng
    discharged = [0] * rng
    gas = [0] * rng
    overhead = [0] * rng
    inbattery_list = [0] * rng

    inbattery = 0
    overhead_count = 0

    for hour in range(rng):
        wind[hour] = (wind[hour]) * wind_multiplier
        solar[hour] = (solar[hour]) * solar_multiplier

        if load[hour] > wind[hour] + solar[hour]:
            if load[hour] - wind[hour] - solar[hour] < inbattery:
                discharged[hour] = load[hour] - (wind[hour] + solar[hour])
                inbattery -= discharged[hour]
                inbattery_list[hour] = inbattery

            else:
                discharged[hour] = inbattery
                inbattery = 0
                gas[hour] = load[hour] - (wind[hour] + solar[hour]) - discharged[hour]
                inbattery_list[hour] = inbattery

        else:
            if wind[hour] + solar[hour] - load[hour] < capacity_storage - inbattery:
                charged[hour] = wind[hour] + solar[hour] - load[hour]
                inbattery = inbattery + wind[hour] + solar[hour] - load[hour]
                inbattery_list[hour] = inbattery

            else:
                charged[hour] = capacity_storage - inbattery
                inbattery = capacity_storage
                overhead[hour] = wind[hour] + solar[hour] - load[hour] - charged[hour]
                inbattery_list[hour] = inbattery
                overhead_count += 1

    if sum(charged) == 0:
        lcoe_storage = 0
    else:
        lcoe_storage = price_kwh_storage * 1000 * pow(discount_rate_storage, years_storage) / (sum(charged) / capacity_storage * years_storage)

    overhead_wind = sum(overhead) * sum(wind) / (sum(solar) + sum(wind))
    overhead_solar = sum(overhead) * sum(solar) / (sum(solar) + sum(wind))
    gas_ratio = sum(gas) / (sum(load))
    #lcoe = (wind_capacity * wind_price + solar_capacity * solar_price + price_kwh_storage * capacity_storage * pow(discount_rate_storage, years_storage) / 1000 + max(gas) * gas_price + max(gas) * gas_ratio * 7.5) / \
    #       ((sum(wind) - overhead_wind + sum(solar) - overhead_solar + (sum(gas))) * years_storage) * 1000000
    lcoe = (112 + wind_capacity * wind_price + solar_capacity * solar_price + price_kwh_storage * capacity_storage * pow(discount_rate_storage, years_storage) / 1000 + max(gas) * gas_price + max(gas) * gas_ratio * 8) / (sum(load) * years_storage) * 1000000
    #lcoe_wind_corr = lcoe_wind + lcoe_wind * (overhead_wind / sum(load))
    #lcoe_solar_corr = lcoe_solar + lcoe_solar * (overhead_solar / sum(load))
    #lcoe = (sum(wind) * lcoe_wind_corr + sum(solar) * lcoe_solar_corr + sum(gas) * lcoe_gas + sum(discharged) * lcoe_storage) / sum(load)
    overhead_ratio = sum(overhead) / (sum(wind) + sum(solar) + sum(gas))

    return lcoe, overhead_ratio, gas_ratio


def values_func(i, wind, solar, load, charged, discharged, gas, overhead, overhead_count, capacity_storage, wind_price, solar_price, gas_price, price_kwh_storage, discount_rate_storage, years_storage, wind_multiplier, solar_multiplier):
    
    wind_capacity = 102.5 * wind_multiplier  # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    solar_capacity = 55 * solar_multiplier
    values = []
    gas_ratio = sum(gas) / (sum(load))
    # расчёт LCOE
    if sum(charged) == 0 or capacity_storage == 0:
        lcoe_storage = 0
    else: 
        lcoe_storage = price_kwh_storage * 1000 * pow(discount_rate_storage, years_storage) / (sum(charged) / capacity_storage * years_storage)
    #overhead_wind = sum(overhead) * sum(wind) / (sum(solar) + sum(wind))
    #overhead_solar = sum(overhead) * sum(solar) / (sum(solar) + sum(wind))
    lcoe = (112 + wind_capacity * wind_price + solar_capacity * solar_price + price_kwh_storage * capacity_storage * pow(discount_rate_storage, years_storage) / 1000 + max(gas) * gas_price + max(gas) * gas_ratio * 8) / (sum(load) * years_storage) * 1000000

    #lcoe_wind_corr = lcoe_wind + lcoe_wind * (overhead_wind/sum(load))
    #lcoe_solar_corr = lcoe_solar + lcoe_solar * (overhead_solar/sum(load))
    #lcoe = (sum(wind) * lcoe_wind_corr + sum(solar) * lcoe_solar_corr + sum(gas) * lcoe_gas + sum(discharged) * lcoe_storage) / sum(load)

    values.append(u'Сценарий %s' % str(i + 1))
    values.append(sprint('capacity storage', capacity_storage, ' ГВт*ч'))
    values.append(sprint('wind multi', wind_multiplier))
    values.append(sprint('solar multi', solar_multiplier))
    values.append(' ')
    if capacity_storage == 0:
        values.append('0')
    else:
        values.append(sprint('storage utilization', sum(charged) / capacity_storage, ' шт.'))
    values.append(sprint('LCOE', lcoe, ' $/МВт*ч'))
    values.append(sprint('LCOE of storage electricity', lcoe_storage, ' $/МВт*ч'))
    values.append(sprint('overhead_ratio', sum(overhead) / (sum(wind) + sum(solar) + sum(gas)) * 100, '%'))
    values.append(' ')
    values.append(sprint('wind installed', wind_capacity, ' ГВт'))
    values.append(sprint('solar installed', solar_capacity, ' ГВт'))
    values.append(sprint('max_gas', max(gas), ' ГВт'))
    values.append(sprint('total installed', solar_capacity + wind_capacity + max(gas), ' ГВт'))
    values.append(sprint('real installed', 488, ' ГВт'))
    values.append(' ')
    values.append(sprint('max_wind', max(wind), ' ГВт'))
    values.append(sprint('max_solar', max(solar), ' ГВт'))
    values.append(sprint('max_load', max(load), ' ГВт'))
    values.append(' ')
    values.append(sprint('wind_ratio', sum(wind)/ (sum(wind) + sum(solar) + sum(gas)) * 100, '%'))
    values.append(sprint('solar_ratio', sum(solar)/ (sum(wind) + sum(solar) + sum(gas)) * 100, '%'))
    values.append(sprint('gas_ratio', sum(gas)/ (sum(wind) + sum(solar) + sum(gas)) * 100, '%'))
    values.append(sprint('storage_ratio', sum(charged) / (sum(wind) + sum(solar) + sum(gas)) * 100, '%'))
    values.append(' ')

    if wind_capacity == 0:
        values.append('0')
    else:
        values.append(sprint('kium wind', 100 * sum(wind) / (wind_capacity * 24 * 365), '%'))
    if solar_capacity == 0:
        values.append('0')
    else:
        values.append(sprint('kium solar', 100 * sum(solar) / (solar_capacity * 24 * 365), '%'))
    if max(gas) == 0:
        values.append('0')
    else:
        values.append(sprint('kium gas', 100 * sum(gas) / (max(gas) * 24 * 365), '%'))
    
    values = '\n'.join(values)
    values = u'%s' % values
    
    return values


def draw_renew(scenarios_count, wind_multiplier, solar_multiplier, capacity_storage, wind_price, solar_price, gas_price, price_kwh_storage,
               discount_rate_storage, years_storage, start_date, end_date, *args):

    import matplotlib  # импорт библиотеки рисования графика
    matplotlib.rc('font', family='DejaVu Sans')  # шрифт с поддержкой русского языка
    matplotlib.use('agg')  # при необходимости можно убрать для sagemath взамен %inline
    import matplotlib.pyplot as plt
    import sys
    reload(sys)
    sys.setdefaultencoding('utf-8')

    if is_float(wind_multiplier[0]) is False or is_float(solar_multiplier[0]) is False or is_float(capacity_storage[0]) is False:
        wind_multiplier = 0
        solar_multiplier = 0
        capacity_storage = 0

    if wind_multiplier[0] < 0 or solar_multiplier[0] < 0 or capacity_storage[0] < 0:
        wind_multiplier = [0]
        solar_multiplier = [0]
        capacity_storage = [0]

    if start_date > end_date or start_date < 0 or end_date > 365:
        start_date = 0 * 24
        end_date = 365 * 24
    else:
        start_date = int(start_date * 24)
        end_date = int(end_date * 24)

    # чтение из файла, обработка массивов

    if args:
        filename = args[0]
    else:
        filename = 'png/renew.png'
    load, wind, solar = read_csv('data/renew.csv', 3)
    wind = list(map(float, wind))
    solar = list(map(float, solar))
    load = list(map(float, load))
    

    # создание заголовков для таблицы
    
    titles = ['Ёмкость аккумуляторов', 'Мультипликатор ветра', 'Мультипликатор солнца', ' ', 'Циклы зарядки/разрядки', 'LCOE', 'LCOS',
              'Потери (перегрузы)', ' ', 'Ветер, установлено', 'Солнце, установлено', 'Газ, макс.', 'Суммарно установлено', 'Реально установлено, 2015г', ' ', 'Ветер, макс.', 'Солнце, макс.', 'Потребление, макс.', ' ', 'Доля ветра',
              'Доля солнца', 'Доля газа', 'Доля аккумуляции', ' ', 'КИУМ ветра', 'КИУМ солнца', 'КИУМ газа']
    titles = '\n'.join(titles)
    titles = u'%s' % titles
    
    note = u'Ветер и солнце = выровненная генерация по основным европейским странам, имитирующая возможность перетоков э/э между ними'
    
    # вычисление данных для графика и первого столбца
    
    wind_multiplied, solar_multiplied, gas, charged, discharged, inbattery_list, capacity_storage, values1 = \
        calculate(0, wind, solar, load, wind_multiplier, solar_multiplier, capacity_storage, wind_price, solar_price, gas_price,
                  price_kwh_storage, discount_rate_storage, years_storage)
    
    # обрезка массивов для графика

    wind_multiplied = list(wind_multiplied[start_date:end_date])
    solar_multiplied = list(solar_multiplied[start_date:end_date])
    gas = list(gas[start_date:end_date])
    charged = list(charged[start_date:end_date])
    discharged = list(discharged[start_date:end_date])
    inbattery_list = list(inbattery_list[start_date:end_date])
    load_chart = list(load[start_date:end_date])
    dates = list(generate_date_range('2015-01-01 00:00', 24*365, 'hour'))
    dates = list(dates[start_date:end_date])

    # создание рисунка с двумя графиками и первого графика
        
    fig = plt.figure(figsize=(16, 24))
    fig.subplots_adjust(top=0.95, bottom=0.35)
    chart1 = fig.add_subplot(211)  # график и его расположение
    
    plt.xticks(rotation=25)
    chart1.grid()  # сетка для графика
    chart1.plot(dates, wind_multiplied, color='b', linewidth=1, label=u'Ветер')
    chart1.plot(dates, solar_multiplied, color='#ffcc00', linewidth=1, label=u'Солнце')
    chart1.plot(dates, gas, color='c', label=u'Газ')
    chart1.plot(dates, charged, color='g', linewidth=1, label=u'Зарядка')
    chart1.plot(dates, discharged, color='r', linewidth=1, label=u'Разрядка')
    chart1.plot(dates, load_chart, ':', color='k', label=u'Потребление')
    chart1.legend()  # добавление и расположение легенд
    chart1.legend(loc='upper left')
    chart1.set_ylabel(u'ГВт')
    chart1.set_title(u'Генерация, аккумуляция, потребление')
    
    # создание второго графика
    
    chart2 = fig.add_subplot(212)  # график и его расположение
    plt.xticks(rotation=25)
    chart2.grid()   # сетка для графика
    chart2.plot(dates, inbattery_list, color='r', linewidth=2)
    chart2.set_ylabel(u'ГВт*ч')
    chart2.set_title(u'Уровень заряда аккумуляторов. Ёмкость = %s ГВт*ч' % capacity_storage[0])

    # формирование и вставка остальных столбцов таблицы (при наличии)
    plt.figtext(0.1, 0.04, titles)
    plt.figtext(0.1, 0.29, note)
    plt.figtext(0.85, 0.31, u'"Селадо"', size=12, style='italic')
    plt.figtext(0.35, 0.04, values1)
    text_x_coordinate = 0.5
    if scenarios_count > 1:
        for i in range(1, scenarios_count):
            values2 = calculate(i, wind, solar, load, wind_multiplier, solar_multiplier, capacity_storage, wind_price, solar_price, gas_price, price_kwh_storage, discount_rate_storage, years_storage)
            plt.figtext(text_x_coordinate, 0.04, values2)
            text_x_coordinate += 0.15

    plt.savefig(filename)

