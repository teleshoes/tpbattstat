/**************************************************************************
 *  TPBattStatApplet v0.1
 *  Copyright 2011 Elliot Wolk
 **************************************************************************
 *  This file is part of TPBattStatApplet.
 *
 *  TPBattStatApplet is free software: you can redistribute it and/or
 *  modify it under the terms of the GNU General Public License as
 *  published by the Free Software Foundation, either version 3 of the
 *  License, or (at your option) any later version.
 *
 *  TPBattStatApplet is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
 *************************************************************************/

#include "tpbattstat-applet.h"
#include "tpbattstat-battinfo.h"
#include "tpbattstat-prefs.h"

int
read_battery_prop(int battery_id, char *property)
{
    int buflen = 256;
    char *buf = malloc(buflen);

    if(battery_id < 0)
        sprintf(buf, "%s/%s", smapi_dir, property);
    else
        sprintf(buf, "%s/BAT%d/%s", smapi_dir, battery_id, property);

    FILE *f = fopen(buf, "r");
    
    if(f == NULL)
    {
        buf[0] = '\0';
    }
    else
    {
        char *str = fgets(buf, buflen, f);
        fclose(f);
        if(str == NULL)
        {
            buf[0] = '\0';
        }
    }
    
    //chomp
    int i;
    for(i=0; i<buflen-1; i++)
    {
        if(buf[i] == '\n' || buf[i] == '\0')
            break;
    }
    buf[i] = '\0';

    int res;
    if(strcmp(property, "state") == 0)
    {
        if(strcmp(buf, "charging") == 0)
            res = CHARGING;
        else if(strcmp(buf, "discharging") == 0)
            res = DISCHARGING;
        else
            res = IDLE;
    }
    else
      res = atoi(buf);
    
    g_free(buf);
    return res;
}

int
write_battery_prop(int battery_id, char *property, char *value)
{
    int buflen = 256;
    char *buf = malloc(buflen);

    if(battery_id < 0)
        sprintf(buf, "%s/%s", smapi_dir, property);
    else
        sprintf(buf, "%s/BAT%d/%s", smapi_dir, battery_id, property);

    FILE *f = fopen(buf, "w");
    if(f == NULL)
    {
        char *cmd = malloc(buflen+256);
        sprintf(cmd, "gksudo chmod a+w %s", buf);
        FILE *p = popen(cmd, "r");
        pclose(p);

        f = fopen(buf, "w");
    }
    
    if(f == NULL)
    {
        return;
    }
    else
    {
        fprintf(f, "%s", value);
        fclose(f);
    }
    g_free(buf);
}

void
get_battery(Battery *bat, int battery_id)
{
    bat->id = battery_id;
    bat->installed =
            read_battery_prop(battery_id, "installed");
    bat->force_discharge =
            read_battery_prop(battery_id, "force_discharge");
    bat->inhibit_charge_minutes =
            read_battery_prop(battery_id, "inhibit_charge_minutes");
    bat->remaining_percent =
            read_battery_prop(battery_id, "remaining_percent");
    bat->power_avg =
            read_battery_prop(battery_id, "power_avg");
    bat->state =
            read_battery_prop(battery_id, "state");
}

void
get_battery_status(BatteryStatus* status)
{
    status->ac_connected = 
            read_battery_prop(-1, "ac_connected");
    get_battery(status->bat0, 0);
    get_battery(status->bat1, 1);
}

int
perhaps_force_discharge(BatteryStatus *status,
        enum DischargeStrategy strategy, int leapfrogThreshold)
{
    int discharge0 = status->bat0->state == DISCHARGING;
    int discharge1 = status->bat1->state == DISCHARGING;
    
    int percent0 = status->bat0->remaining_percent;
    int percent1 = status->bat1->remaining_percent;

    int force_discharge =
        !status->ac_connected &&
        status->bat0->installed &&
        status->bat1->installed &&
        strategy != DISCHARGE_SYSTEM;

    int force0 = 0;
    int force1 = 0;
    if(force_discharge)
    {
        if(strategy == DISCHARGE_LEAPFROG)
        {
            if(discharge0)
            {
                if(percent1 - percent0 > leapfrogThreshold)
                    force1 = 1;
                else if(percent0 > leapfrogThreshold)
                    force0 = 1;
            }
            else if(discharge1)
            {
                if(percent0 - percent1 > leapfrogThreshold)
                    force0 = 1;
                else if(percent1 > leapfrogThreshold)
                    force1 = 1;
            }
            else if(percent0 > leapfrogThreshold && percent0 > percent1)
                force0 = 1;
            else if(percent1 > leapfrogThreshold && percent1 > percent0)
                force1 = 1;
        }
        else if(strategy == DISCHARGE_CHASING)
        {
            if(percent0 > percent1)
                force0 = 1;
            else if(percent1 > percent0)
                force1 = 1;
        }
    }

    int prevforce0 = status->bat0->force_discharge;
    int prevforce1 = status->bat1->force_discharge;
 
    if(prevforce0 != force0 || prevforce1 != force1)
    {
        char *buf = malloc(1);
        if(prevforce0 != force0)
        {
            sprintf(buf, "%d", force0);
            write_battery_prop(0, "force_discharge", buf);
        }
        if(prevforce1 != force1)
        {
            sprintf(buf, "%d", force1);
            write_battery_prop(1, "force_discharge", buf);
        }
        g_free(buf);
    }
}

/* Uninhibit charging the chosen battery, and inhibit the other battery if:
 *  chosen battery is inhibited
 *   OR
 *  chosen battery is not charging, and other battery is not inhibited
 */
void
ensure_charging(int battery, BatteryStatus* status)
{
    int previnhib0 = status->bat0->inhibit_charge_minutes;
    int previnhib1 = status->bat1->inhibit_charge_minutes;

    int charge0 = status->bat0->state == CHARGING;
    int charge1 = status->bat1->state == CHARGING;

    if(battery == 0 && (previnhib0 || (!charge0 && !previnhib1)))
    {
        write_battery_prop(0, "inhibit_charge_minutes", "0");
        write_battery_prop(1, "inhibit_charge_minutes", "1");
    }
    else if(battery == 1 && (previnhib1 || (!charge1 && !previnhib0)))
    {
        write_battery_prop(1, "inhibit_charge_minutes", "0");
        write_battery_prop(0, "inhibit_charge_minutes", "1");
    }
}

int
perhaps_inhibit_charge(BatteryStatus *status,
        enum ChargeStrategy strategy, int leapfrogThreshold,
        const int brackets[], int bracketsSize, int bracketsPrefBat)
{
    int never_inhibit =
        !status->ac_connected ||
        !status->bat0->installed ||
        !status->bat1->installed ||
        strategy == CHARGE_SYSTEM;

    int charge0 = status->bat0->state == CHARGING;
    int charge1 = status->bat1->state == CHARGING;

    int percent0 = status->bat0->remaining_percent;
    int percent1 = status->bat1->remaining_percent;

    if(never_inhibit)
    {
        if(status->bat0->inhibit_charge_minutes)
            write_battery_prop(0, "inhibit_charge_minutes", "0");
        if(status->bat1->inhibit_charge_minutes)
            write_battery_prop(1, "inhibit_charge_minutes", "0");
    }
    else if(strategy == CHARGE_LEAPFROG)
    {
        if(percent1 - percent0 > leapfrogThreshold)
            ensure_charging(0, status);
        else if(percent0 - percent1 > leapfrogThreshold)
            ensure_charging(1, status);
    }
    else if(strategy == CHARGE_CHASING)
    {
        if(percent1 > percent0)
            ensure_charging(0, status);
        else if(percent0 > percent1)
            ensure_charging(1, status);
    }
    else if(strategy == CHARGE_BRACKETS)
    {
        int prefBat = bracketsPrefBat;
        int unprefBat = 1 - prefBat;
        int percentPref = prefBat == 0 ? percent0 : percent1;
        int percentUnpref = prefBat == 1 ? percent0 : percent1;
        int i;
        for(i=0; i<bracketsSize; i++)
        {
            int bracket = brackets[i];
            if(percentPref < bracket){
                ensure_charging(prefBat, status);
                break;
            }
            else if(percentUnpref < bracket){
                ensure_charging(unprefBat, status);
                break;
            }
        }
    }
}
