/*
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License.  You may obtain a copy
 * of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 */
package org.openstack.sahara.examples.pig;

import org.apache.pig.PrimitiveEvalFunc;

public class StringCleaner extends PrimitiveEvalFunc<String, String>
{
    public String exec(String input) {
        // Useless example which removes all but few basic latin characters
        // and separators
        return input.replaceAll("[^A-Za-z0-9-_]+", "");
    }
}
