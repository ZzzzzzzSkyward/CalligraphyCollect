<template>
  <div class="app-container">
    <el-tooltip placement="top" content="返回顶部" effect="light">
      <el-backtop :right="20" :bottom="20" />
    </el-tooltip>
    <el-container>
      <el-header>
        <h1 class="page-nav-item" :class="currentApp == 'collect' ? 'selected' : ''" @click="RunCollectApp"><span>
            书法集字
          </span></h1>
        <h1 v-if="false" class="page-nav-item" :class="currentApp == 'priority' ? 'selected' : ''"
          @click="RunPriorityApp"><span>
            碑帖优先级
          </span></h1>
        <h1 class="page-nav-item" :class="currentApp == 'ids' ? 'selected' : ''" @click="RunIDSApp"><span>
            IDS
          </span></h1>
        <h1 class="page-nav-item" :class="currentApp == 'import' ? 'selected' : ''" @click="RunImportApp"><span>
            导入
          </span></h1>
      </el-header>
      <el-main>
        <div class="search-container" v-if="currentApp == 'collect'">
          <label class="vnt-input">
            <el-autocomplete ref="textInputRef" :fetch-suggestions="fetchHistory" clearable @select="handleSelect"
              maxlength="100" v-model="searchQuery" @input="DontperformSearch" @keyup.enter="performSearch"
              placeholder="空格隔开字符串(正则表达式)，最长100" class="vnt-input__control"
              @selectionchange="OnSearchTextSelectionChange" />
          </label>
          <button type="primary" class="vnt-button vnt-button--primary custom-button-short" @click="ToTraditional">
            转繁体
          </button>
          <button @click="performSearch" class="vnt-button">搜</button>
          <div v-if="showPopover && similarChars.length > 0" class="popover-menu"
            :style="{ left: popOverLeft.toString() + 'px' }">
            <ul>
              <li v-for="(char, index) in similarChars" :key="index" @click="insertChar(char)"
                style="cursor: pointer; padding: 4px 8px;">
                {{ char }}
              </li>
            </ul>
          </div>
        </div>

        <div v-show="currentApp == 'collect' && searchResultCache.length > 0" class="results-container"
          v-loading="IsSearching">
          <header class="search-result-header">
            <h2><span>
                作品{{ searchResultCache.length }}
              </span>&nbsp;
              <span>匹配{{ submittedMaxHit }}~{{ maxSubqueryCount }}/{{
                submittedSubqueryCount
              }}</span>
            </h2>
            <div>
              <button class="vnt-button" @click="ChangeView">
                切换视图
              </button>
              <el-tooltip placement="top" content="导出统计信息" effect="light">
                <button class="vnt-button vnt-button--primary" @click="ExportSearchToCSV">
                  导出csv
                </button>
              </el-tooltip>
              <button class="vnt-button vnt-button--primary hidden" style="display: none;"
                @click="ExportSearchToHTML">导出html(含行列坐标)</button>
            </div>
          </header>
          <ul v-infinite-scroll="LoadMore">
            <li v-for="(result, index) in searchResults" :key="result.name" class="search-result-item"
              :class="result.chars.length ? '' : 'no-image'"
              v-memo="[searchResults.length, submittedQuery, viewType, ForceRefreshSearchResultView]">
              <div class="result-title" @click="OpenPanel($event, result)">
                <h6>
                  <p class="result-info"><span class="work-index">{{ index + 1 }} </span><span
                      class="text-truncate-scroll">
                      {{ result.name }}
                    </span>
                  </p>
                  <p class="result-info-2">
                    <span class="work-owner" v-if="result.owner">{{ result.owner }}</span><span>|</span>
                    <span class="work-id" v-if="result.id"> {{ result.id }}</span><span>|</span>
                    <span class="work-match" v-if="result.match_count">命中{{ result.match_count }}</span>
                  </p>
                </h6>
                <ul v-if="result.chars.length" class="char-match-list">
                  <li v-for="match in result.chars" :key="match.char" class="char-match-item">
                    <el-image class="result-image lloading" @load="OnImageLoad" @error="OnImageLoad"
                      :src="match.urls[0]" v-if="match.urls.length" fit="contain"> <template #error>
                        <div class="image-slot">
                          <el-tooltip placement="top" :content="match.urls[0]" effect="light">
                            <span>{{ match.char }}</span>
                          </el-tooltip>
                        </div>
                      </template>
                    </el-image>
                  </li>
                </ul>
              </div>
              <div class="match-details" v-if="viewType == 0">
                <el-collapse v-model="activeNames">
                  <el-collapse-item v-if="result.chars.length" title="图片" name="0" class="image-match">
                    <el-table :data="result.chars" max-height="500">
                      <el-table-column prop="char" label="字符" width="2em" class="image-match-col-char" />
                      <el-table-column label="图片">
                        <template #default="scope">
                          <div class="image-match-list">
                            <div v-for="(url, uindex) in scope.row['urls']" class="image-match-item">
                              <div>
                                <el-image :src="url" class="image-match-img" :alt="url" loading="lazy"
                                  crossorigin="anonymous" @click="$preview(url, scope.row['urls'])" fit="contain">
                                  <template #error>
                                    <div class="image-slot">
                                      <el-tooltip placement="top" :content="url" effect="light">
                                        <span>{{ scope.row['char'] }}</span>
                                      </el-tooltip>
                                    </div>
                                  </template>
                                </el-image>
                              </div>
                            </div>
                          </div>
                        </template>
                      </el-table-column>
                    </el-table>
                  </el-collapse-item>
                </el-collapse>
                <el-collapse v-model="activeNames">
                  <el-collapse-item title="文本" name="2" class="text-match">
                    <p v-html="highlightMatch(result, submittedQuery.value)" @mouseup="OnSelectChangeOnText(result)">
                    </p>
                  </el-collapse-item>
                </el-collapse>
              </div>
            </li>
          </ul>
        </div>
        <div v-show="currentApp == 'priority'" class="priority-container">
          <el-container>
            <el-header>
              <h2>注意事项</h2>
              <div>
                <p>1. 必须先保存一次才能排序</p>
                <p>2. 保存到浏览器缓存中</p>
                <p>3. 要持续存储或者在浏览器间迁移，可导出/导入</p>
              </div>
              <h2>搜索选项</h2>
              <div>
                <label class="vnt-checkbox"><input type="checkbox" class="vnt-checkbox__input" @change="SaveGeneralSave"
                    v-model="IsAlwaysSortByPriority">
                  <span class="vnt-checkbox__tick"></span> <span class="vnt-checkbox__text">始终按优先级排序</span></label>
                <label class="vnt-checkbox"><input type="checkbox" class="vnt-checkbox__input" @change="SaveGeneralSave"
                    v-model="IsHideNoPriority"> <span class="vnt-checkbox__tick"></span> <span
                    class="vnt-checkbox__text">始终隐藏无优先级条目</span></label>
              </div>
            </el-header>
            <el-main v-loading="IsLoading_Priority" element-loading-text="加载中...">
              <h2>优先级表</h2>
              <div class="search-container">
                <label class="vnt-input">
                  <el-input clearable maxlength="100" v-model="priorityQuery" @input="DontperformSearch"
                    @keyup.enter="performPrioritySearch" placeholder="字符串(正则表达式)，最长100" class="vnt-input__control" />
                </label>
                <button @click="SavePriority" class="vnt-button">保存&应用</button>
                <button @click="ExportPriority" class="vnt-button">导出json</button>
                <button @click="ImportPriority" class="vnt-button">导入json</button>
              </div>
              <VxeTable class="priority-table" :data="priorityData" :column-config="{ resizable: true }"
                TODO="修复无法验证数字的bug" :edit-rules="{ priority: [{ type: 'number', validator: ValidateNumber }] }"
                :edit-config="editConfig" :row-config="{ isHover: true }" :show-overflow="false"
                :scroll-y="{ enabled: true, gt: 0 }" :sort-config="sortConfig" height="auto" style="overflow-y:hidden;">
                <VxeColumn field="id" title="ID"></VxeColumn>
                <VxeColumn sortable field="name" title="名称"></VxeColumn>
                <VxeColumn sortable field="owner" title="作者"></VxeColumn>
                <VxeColumn sortable field="wenti" title="文体"></VxeColumn>
                <VxeColumn sortable sort-type="number" field="priority" title="优先级"
                  :edit-rules="{ type: 'number', validator: ValidateNumber }" :scroll-y="{ enabled: true, gt: 0 }"
                  :edit-render="{ name: 'input', attrs: { type: 'text' } }">
                  <template #edit="{ row }">
                    <input v-model="row.priority" type="text" @change="ValidateAndSavePriority">
                  </template>
                </VxeColumn>
              </VxeTable>
              <hr />
            </el-main>
          </el-container>
        </div>
        <div v-show="currentApp == 'import'" class="import-container">
          <el-container>
            <el-header>
              <h2>导入新碑帖</h2>
            </el-header>
            <el-main>
              <p>导入说明</p>
              <p>1.为支持完全的功能，并实现最大化的可自定义操作，不在前端制定导入规范，而是用json作为存储格式。</p>
              <p>2.本项目路径src/back/data/存储了索引与本地图片。</p>
              <p>3.本项目路径src/back/data/index存储了索引，格式是json，两个大文件压缩为.json.zip存储。</p>
              <p>4.规定索引数据结构如下，按照此格式制作*.json即可被自动识别。</p>
              <p>5.后端将按照文件名升序依次读取每个自定义json文件，一个json文件可以只有一个碑帖，也可以由多个。</p>
              <el-collapse v-model="Collapse0Show1">
                <el-collapse-item title="数据结构" name="0">
                  <ol class="doc">
                    <li>
                      <p><code>name</code>
                      <pre>String</pre>
                      </p>
                      <p>碑帖名</p>
                    </li>
                    <li>
                      <p><code>sw</code>
                      <pre>String</pre>
                      </p>
                      <p>文本</p>
                    </li>
                    <li>
                      <p><code>owner</code>
                      <pre>String</pre>
                      </p>
                      <p>作者</p>
                    </li>
                    <li>
                      <p><code>detail</code>
                      <pre>Array[Array]</pre>
                      </p>
                      <p>细节</p>
                      <p>只用到了detail[0]</p>
                    </li>
                    <ol>
                      <li>
                        <p><code>detail[0]</code>
                        <pre>Array[Object]</pre>
                        </p>
                        <p>碑帖图片列表</p>
                      </li>
                      <ol>
                        <li>
                          <p><code>detail[0][i].url</code>
                          <pre>String</pre>
                          </p>
                          <p>图片网址或者本地路径</p>
                          <p>本地路径如"./data/images/123.jpg"</p>
                          <p>网址如"https://www.shufazidian.com/s.php"</p>
                        </li>
                        <li>
                          <p><code>detail[0][i].char</code>
                          <pre>Array[Object]</pre>
                          </p>
                          <p>单字列表</p>
                        </li>
                        <ol>
                          <li>
                            <p><code>detail[0][i].char[j].char</code>
                            <pre>String</pre>
                            </p>
                            <p>单字字符</p>
                          </li>
                          <li>
                            <p><code>detail[0][i].char[j].pos</code>
                            <pre>String</pre>
                            </p>
                            <p>单字坐标，以图片左上角为原点，认为是一个矩形</p>
                            <p>[左，上，右，下]</p>
                          </li>
                        </ol>
                      </ol>
                    </ol>
                  </ol>
                </el-collapse-item>
                <el-collapse-item title="示例" name="1">
                  <el-form :model="importExample" label-width="auto">
                    <el-form-item label="碑帖名">
                      <el-input v-model="importExample.Name" @change="importRender" />
                    </el-form-item>
                    <el-form-item label="作者">
                      <el-input v-model="importExample.Owner" @change="importRender" />
                    </el-form-item>
                    <el-form-item label="文本">
                      <el-input v-model="importExample.Text" @change="importRender" />
                    </el-form-item>
                    <el-form-item label="图片地址">
                      <el-input v-model="importExample.Url" @change="importRender" />
                    </el-form-item>
                    <button type="primary" class="vnt-button vnt-button--primary" @click="importSubmit">添加</button>
                    <button type="primary" class="vnt-button vnt-button--primary" @click="importImport">导入JSON</button>
                    <button type="primary" class="vnt-button vnt-button--primary" @click="importExport">导出文本</button>
                    <button type="secondary" class="vnt-button vnt-button--secondary" @click="importClear">清空结果</button>
                    <el-form-item label="预览或结果">
                      <p>可自由修改再导出，但在添加、导入后会重置文本框到初始状态</p>
                      <textarea class="import-preview" ref="importPreview"></textarea>
                    </el-form-item>
                  </el-form>
                </el-collapse-item>
              </el-collapse>
            </el-main>
          </el-container>
        </div>
        <div class="status-container" v-show="currentApp == 'collect'">
          <div v-if="searchQuery && IsSearching" class="no-results">
            <p>搜索中</p>
            <div class="loading-widget" v-loading="true"></div>
          </div>
          <div v-else-if="searchResults.length == 0 && !IsSearching" class="no-results">
            <p>结果为空</p>
          </div>
        </div>
        <div v-show="currentApp == 'ids'" class="ids-container">
          <el-container>
            <el-header>
              <h2>Unicode码</h2>
            </el-header>
            <el-main>
              <el-form v-model="idsQuery" label-width="auto">
                <el-form-item label="字符">
                  <el-input v-model="idsQuery.char" @keyup.enter="performIdsSearch" placeholder="输入Unicode码"></el-input>
                </el-form-item>
                <el-form-item label="ID">
                  <el-input v-model="idsQuery.id" @keyup.enter="performIdsSearch" placeholder="输入碑帖序号"></el-input>
                </el-form-item>
              </el-form>
              <p v-html="idsResult_show"></p>
            </el-main>
          </el-container>
        </div>
      </el-main>
      <el-footer>
      </el-footer>
    </el-container>
    <el-drawer v-model="drawerVisible" :with-header="false" direction="rtl" size="90%" id="detailpanel"
      :before-close="onDrawerClose">
      <div class="card-header">
        <h6>{{ selectedResult.name }}</h6>
        <el-tag>{{ selectedResult.owner }}</el-tag>
      </div>
      <div class="text item">
        <el-row>
          <el-col :span="24">
            <div class="drawer-search-container">
              <el-autocomplete v-model="drawerQueryString" :fetch-suggestions="drawerQuerySearch"
                :trigger-on-focus="true" clearable class="" placeholder="输入单个中文字符以触发自动补全" @select="drawerHandleSelect"
                maxlength="100" />
              <button type="primary" class="vnt-button vnt-button--primary" @click="drawerToTraditional">
                转繁体
              </button>
              <button type="secondary" class="vnt-button vnt-button--secondary" @click="drawerSearchChar">
                搜索
              </button>
            </div>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="24">
            <el-collapse v-model="Show0">
              <el-collapse-item title="文本" name="0" class="text-match">
                <p v-html="highlightMatch(drawerTextContent)" @mouseup="OnSelectChangeOnText(drawerTextContent)">
                </p>
              </el-collapse-item>
            </el-collapse>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="24">
            <el-collapse v-model="Show0">
              <el-collapse-item title="大图" name="1" class="text-match">
                <el-image v-for="(url, index) in selectedResult.images" :key="index" :src="url" class="drawer-image"
                  :alt="url" loading="lazy" crossorigin="anonymous" @click="$preview(url, selectedResult.images)"
                  fit="contain">
                  <template #error>
                    <div class="image-slot">
                      <el-tooltip placement="top" :content="url" effect="light">
                        <span>{{ url }}</span>
                      </el-tooltip>
                    </div>
                  </template>
                </el-image>
              </el-collapse-item>
            </el-collapse>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="24">
            <div class="flex drawer-char-title">
              <strong>字符详情</strong>
              <button type="primary" class="vnt-button vnt-button--primary" @click="clearDrawerChars">
                清除
              </button>
            </div>
            <el-table :data="selectedChars" style="width: 100%" :row-style="drawerCharRow">
              <el-table-column prop="char" label="字符" width="180"></el-table-column>
              <el-table-column label="图片">
                <template #default="scope">
                  <div class="image-match-list">
                    <div v-for="(url, uindex) in scope.row['urls']" class="image-match-item">
                      <el-image :src="url" class="image-match-img" :alt="url" loading="lazy" crossorigin="anonymous"
                        @click="$preview(url, scope.row['urls'])" fit="contain">
                        <template #error>
                          <div class="image-slot">
                            <el-tooltip placement="top" :content="url" effect="light">
                              <span>{{ scope.row['char'] }}</span>
                            </el-tooltip>
                          </div>
                        </template>
                      </el-image>
                    </div>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </el-col>
        </el-row>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { ConvertChinese } from "@/chinese_convert";
import { GetVariable } from "@/variable_convert";
import { ElMessage, ElMessageBox } from "element-plus";
import { h } from "vue";
import { stringify } from 'csv-stringify';
import { FindChineseComponent, FindCharactersWithComponent } from "@/ids_convert";
import { VxeButton } from 'vxe-pc-ui';
import { VxeTable, VxeColumn } from 'vxe-table';
const server_host = "http://localhost:5012"
const server_url = `${ server_host }/api/query?q=%s`;
const entry_url = `${ server_host }/api/getentry`;
const image_construct_url = `${ server_host }/`
const activeNames = ref( [ "0" ] );
const searchQuery = ref( "" );
const searchResults = ref( [] );
const drawerVisible = ref( false );
const drawerQueryString = ref( '' ); // 绑定搜索框的值
const drawerTextContent = ref( { sw: '' } );
const submittedQuery = ref( "" );
const submittedSubqueryCount = ref( 0 );
const maxSubqueryCount = ref( 0 );
const IsSearching = ref( false );
const IsLoading_Priority = ref( true );
const searchResultCache = ref( [] );//cache the last one
const viewType = ref( 1 );
const currentApp = ref( "collect" );//collect or priority
const priorityData = ref( [] );
const Show0 = ref( [ 0 ] );
const Collapse0Show1 = ref( [ '1' ] );
const priorityQuery = ref( "" );
const priorityDataCache = ref( [] );
const IsAlwaysSortByPriority = ref( false );
const IsHideNoPriority = ref( false );
const submittedMaxHit = ref( 0 );
const selectedResult = ref( {} );
const idsQuery = ref( { char: "", id: "4822" } );
const idsResult = ref( "" );
const idsResult_show = ref( "" );
const handleSelect = ( item ) => { };
const showPopover = ref( false );
const similarChars = ref( [] );
const textInputRef = ref( null );
const popOverLeft = ref( 0 );
const importExample = ref( {
  Name: "",
  Owner: "",
  Text: "",
  Url: "",
} );
const importExampleJson = ref( "" );
const importExampleData = [];
const importPreview = ref( null );
const importRender = () => {
  let detail = [ {
    "url": importExample.value.Url,
    "char": []
  } ];
  let data = {
    "name": importExample.value.Name,
    "owner": importExample.value.Owner,
    "sw": importExample.value.Text,
    "detail": [
      detail
    ]
  };
  //importExampleData.push( data );
  importExampleJson.value = JSON.stringify( data, null, 2 );
  importPreview.value.value = importExampleJson.value;
}
const importSubmit = ( e ) => {
  let detail = [ {
    "url": importExample.value.Url,
    "char": []
  } ];
  let data = {
    "name": importExample.value.Name,
    "owner": importExample.value.Owner,
    "sw": importExample.value.Text,
    "detail": [
      detail
    ]
  };
  importExampleData.value.push( data );
  importExampleJson.value = JSON.stringify( importExampleData.value, null, 2 );
  importPreview.value.value = importExampleJson.value;
  e.preventDefault();
  return true;
}
const importClear = ( e ) => {
  importExampleData.value = [];
  importExampleJson.value = JSON.stringify( importExampleData, null, 2 );
  importPreview.value.value = importExampleJson.value;
  e.preventDefault();
  return true;
}
const importImport = ( e ) => {
  readfn = readImportData;
  virtualInput.click();
  e.preventDefault();
  return true;
}
const importExport = ( e ) => {
  const s = JSON.stringify( importPreview.value.value, null, 2 );
  Download( "custom.json", s );
  e.preventDefault();
  return true;
}
const general_save_kv = {
  "IsAlwaysSortByPriority": IsAlwaysSortByPriority,
  "IsHideNoPriority": IsHideNoPriority
};
onMounted( () => {
  LoadGeneralSave();
} )
onUnmounted( () => {
  SaveGeneralSave();
} )
const UpdateIDSResult = async ( v, isRaw ) => {
  let uid = 'uid' + Math.random().toString( 7 ).substring( 2, 15 ) + Math.random().toString( 36 ).substring( 2, 15 );
  idsResult.value += isRaw ? v : `<li>
    <span>字符：${ v }</span>
    <span>Unicode：${ v.charCodeAt( 0 ).toString( 16 ).padStart( 4, '0' ).toUpperCase() }</span>
    <div class='number-count'></div>
    <div id=${ uid }></div>
    `;
  let omitted = '<span>数量：</span><p style="display:inline">0</p>';
  if ( !isRaw ) {
    await fetch( `${ server_host }/api/get_text?id=${ idsQuery.value.id }` ).then( response => response.text() ).then( text => {
      let r = new Set();
      FindCharactersWithComponent( v, text, r );
      for ( let v1 of r )
        fetch( `${ server_host }/api/getimage?id=${ idsQuery.value.id }&char=${ v1 }` ).then( ( response ) => response.json() ).then( j => {
          for ( let i of j ) {
            let img = `<img src="${ image_construct_url }${ i }" alt="image" onerror='this.style.display="none";'>`;
            idsResult.value += img;
            //div.parentElement.querySelector( 'p' ).innerHTML = `<span>${ div.children.length }</span>`;
          }
        } );
    } ).finally( () => {
      idsResult.value + '</li>';
      idsResult_show.value = idsResult.value;
    } );
  }
  return v;
}
const performIdsSearch = async () => {
  idsResult.value = "<ol>";
  await DoSearchIDS( idsQuery.value.char, 0, {}, [] );
  idsResult.value += "</ol>";
  idsResult_show.value = idsResult.value;
  //console.log( idsResult.value );
}
const DoSearchIDS = async ( q, depth, accessed, parent ) => {
  if ( depth > 10 ) return;
  //console.log( "DoSearchIDS", q );
  if ( q.length < 1 ) return;
  if ( parent.includes( q ) ) return;
  await UpdateIDSResult( q );
  let ret = accessed[ q ] || FindChineseComponent( q );
  accessed[ q ] = ret;
  //console.log( ret );
  if ( ret instanceof Set ) {
    ret = Array( ...ret );
  }
  if ( ret.length === 1 ) return;
  //console.log( ret );
  let sub = ret.slice( 1 );
  await UpdateIDSResult( "<ol>", 1 );
  parent.push( q );
  for ( let s of sub ) {
    for ( let j of s.split( ' ' ) )
      DoSearchIDS( j, depth + 1, accessed, parent );
  }
  parent.pop();
  await UpdateIDSResult( "</ol>", 1 );
}
const SaveGeneralSave = () => {
  let save_obj = {};
  for ( let key in general_save_kv ) {
    if ( general_save_kv[ key ].value !== undefined )
      save_obj[ key ] = general_save_kv[ key ].value;
  }
  localStorage.setItem( "calg.general_save", JSON.stringify( save_obj ) );
}
const LoadGeneralSave = () => {
  let save_obj = localStorage.getItem( "calg.general_save" );
  if ( save_obj ) {
    try {
      save_obj = JSON.parse( save_obj );
      for ( let key in general_save_kv ) {
        if ( key in save_obj )
          general_save_kv[ key ].value = save_obj[ key ];
      }
    } catch ( e ) {
      console.error( `LoadGeneralSave error: ${ e }` );
    }
  }
}
const OnImageLoad = ( e ) => {
  e.target.parentElement.classList.remove( "lloading" );
}
const editConfig = {
  trigger: 'click',
  enabled: true,
  mode: 'cell',
  beforeEditMethod ( { row, rid, col, cid } ) {

    return true
  }
}
const sortConfig = {
  trigger: 'cell',
  orders: [ 'desc', 'asc', null ]
}
const ValidateNumber = ( value ) => {
  if ( value == null || value === '' ) {
    return true;
  }
  const n = parseFloat( value );
  return !isNaN( n ) && isFinite( n );
};
const ChangeView = () => {
  let v = viewType.value;
  if ( v == 0 ) {
    viewType.value = 1;
  }
  else {
    viewType.value = 0;
  }
}
const RunCollectApp = () => {
  currentApp.value = "collect";
}
const RunIDSApp = () => {
  currentApp.value = "ids";
}
const RunImportApp = () => {
  currentApp.value = "import";
}
const RunPriorityApp = () => {
  currentApp.value = "priority";
  if ( priorityData.value.length == 0 ) {
    IsLoading_Priority.value = true;
    fetch( entry_url ).then( ( res ) => {
      return res.json()
    }
    ).then( ( data ) => {
      window.ddd = data;
      if ( data ) {
        data.forEach( ( x ) => {
        } );
        priorityDataCache.value = data;
        LoadPriority();
        priorityData.value = data;
      }
    } ).finally( () => {
      IsLoading_Priority.value = false;
    } );
  }
}
const priority_store_key = "calg.priority_min"
const SavePriority = ( full ) => {
  SyncPriority();
  //only save a min version
  //only save the [id,priority] with priority !== 0
  let saved = [];
  priorityDataCache.value.forEach( ( x ) => {
    if ( x.priority && parseFloat( x.priority ) ) {
      if ( full !== true )
        saved.push( [ x.id, parseFloat( x.priority ) ] );
      else saved.push( [ x.id, x.name, x.owner, x.priority ] );
    }
  } );
  if ( full !== true )
    localStorage.setItem( priority_store_key, JSON.stringify( saved ) );
  return saved;
}
let priority_cache = null;
const GetPriorityMinData = () => {
  if ( priority_cache ) return priority_cache;
  let saved = localStorage.getItem( priority_store_key );
  if ( !saved ) return [];
  priority_cache = JSON.parse( saved );
  return priority_cache;
}
const getpriority = ( id ) => {
  let pr_data = GetPriorityMinData();
  for ( let i = 0; i < pr_data.length; i++ ) {
    if ( pr_data[ i ][ 0 ] == id ) return pr_data[ i ][ 1 ];
  }
  return 0;
}
const LoadPriority = () => {
  priority_cache = null;
  let saved = localStorage.getItem( priority_store_key );
  if ( !saved ) return;
  try {
    let parsed = JSON.parse( saved );
    parsed.forEach( ( x ) => {
      priorityDataCache.value[ x[ 0 ] ].priority = x[ 1 ];
    } );
  } catch ( e ) {
    console.error( "error parsing priority data", e );
    return;
  }
}
const ValidateAndSavePriority = ( event ) => {
  let t = event.target;
  let value = t.value;
  //console.log( "validate and save priority", value );
  //must be a number
  if ( !ValidateNumber( value ) ) {
    t.value = "";
    return;
  }
  //console.log( "sync priority" );
  SyncPriority();
  priority_cache = null;
}
const ApplyPrioritySorting = ( hide_zero ) => {
  let pr_data = GetPriorityMinData();
  let pri = {};
  for ( let i = 0; i < pr_data.length; i++ ) {
    pri[ pr_data[ i ][ 0 ] ] = pr_data[ i ][ 1 ];
  }
  let data = searchResultCache.value;
  if ( hide_zero ) {
    data = data.filter( x => getpriority( x.id ) > 0 );
    searchResultCache.value = data;
  }
  data.sort( ( a, b ) => {
    let aid = a.id;
    let bid = b.id;
    let apr = pri[ aid ] || 0;
    let bpr = pri[ bid ] || 0;
    if ( apr > bpr ) return -1;
    else if ( apr < bpr ) return 1;
    return a.match_count > b.match_count ? -1 : a.match_count < b.match_count ? 1 : 0;
  } );
  searchResults.value = searchResultCache.value.slice( 0, 10 );
  ForceRefreshResult();
}
const SyncPriority = () => {
  let cache = priorityDataCache.value;
  priorityData.value.forEach( ( x ) => {
    let id = x.id;
    let src = cache[ id ];
    if ( !src ) {
      console.error( "no ", id );
      return;
    }
    src.priority = x.priority;
  } )
  priority_cache = null;
}
const customStringify = ( arr ) => {
  const dim2 = arr[ 0 ].length;
  // 首先将整个数组转换为JSON字符串
  const jsonString = JSON.stringify( arr );

  // 将JSON字符串转换为数组字符串
  const arrayString = jsonString.slice( 1, -1 ); // 去掉最外层的方括号

  // 将数组字符串按逗号分割
  const parts = arrayString.split( ',' );

  // 重新构建字符串，使得第一维换行，第二维保持在一行
  let result = '[\n';
  for ( let i = 0; i < parts.length; i++ ) {
    if ( i % dim2 === 0 ) { // 假设每个子数组有两个元素，这里可以根据实际情况调整
      if ( i > 0 ) {
        result += ',\n';
      }
    } else {
      result += ', ';
    }
    result += parts[ i ];
  }
  result += '\n]';

  return result;
}
const ForceRefreshSearchResultView = ref( false );
const ForceRefreshResult = () => {
  ForceRefreshSearchResultView.value = !ForceRefreshSearchResultView.value;
};
const ExportPriority = () => {
  let saved = SavePriority( true );
  let blob = new Blob( [ customStringify( saved ) ], { type: "text/plain;charset=utf-8" } );
  let url = URL.createObjectURL( blob );
  let a = document.createElement( 'a' );
  a.href = url;
  a.download = "priority.json";
  a.click();
  URL.revokeObjectURL( url );
}
let virtualInput = document.createElement( 'input' );
virtualInput.type = "file";
virtualInput.accept = ".json";
let readPriorityData = function ( parsed ) {
  parsed.forEach( ( x ) => {
    let id = x[ 0 ];
    let priority = x[ 3 ];
    if ( priorityDataCache.value[ id ] ) {
      priorityDataCache.value[ id ].priority = priority;
    } else {
      console.error( `ID ${ id } not found` );
    }
  } );
  //clear current edit
  priorityData.value = priorityDataCache.value;
}
let readImportData = function ( parsed ) {
  importExampleData.value = parsed;
  importExampleJson.value = JSON.stringify( importExampleData.value, null, 2 );
  importPreview.value.value = importExampleJson.value;
}
let readfn = readPriorityData;
virtualInput.addEventListener( 'change', ( event ) => {
  const file = event.target.files[ 0 ];
  if ( !file ) return;

  const reader = new FileReader();
  reader.onload = function () {
    try {
      let parsed = JSON.parse( this.result );
      readfn( parsed );
      Success( `导入${ file.name }成功` );
    } catch ( e ) {
      console.error( 'Failed to parse JSON file:', e );
      Alert( '导入的json文件格式不正确或文件损坏' );
    }
  };
  reader.readAsText( file );
} );
const ImportPriority = () => {
  readfn = readPriorityData;
  virtualInput.click();
}//history
////
const historyList = ref( [] );
const fetchHistory = ( queryString, cb ) => {
  const results = queryString
    ? historyList.value.filter( createFilter( queryString ) )
    : historyList.value;
  // call callback function to return suggestions
  cb( results );
};
const createFilter = ( queryString ) => {
  return ( entry ) => {
    return entry.value.indexOf( queryString ) >= 0;
  };
};
let submittedPriorityQuery = "";
const performPrioritySearch = () => {
  let v = priorityQuery.value.trim();
  if ( v.length === 0 ) {
    //restore
    priorityData.value = priorityDataCache.value;
    submittedPriorityQuery = "";
    return;
  }
  //same
  if ( v === submittedPriorityQuery ) return;
  //validate regexp
  if ( !validateRegexp( v ) ) {
    return;
  }
  //console.log( "perform priority search: " + v );
  submittedPriorityQuery = v;
  IsLoading_Priority.value = true;
  SyncPriority();
  //filter any from name,owner
  let filtered = priorityDataCache.value.filter( ( x ) => {
    return x.name.match( RegExp( v ) ) || x.owner.match( RegExp( v ) );
  } );
  priorityData.value = filtered;
  IsLoading_Priority.value = false;
};
const historystorekey = "calg.autocompleteHistory";
const max_history = 30;
const SaveHistory = function () {
  //console.log( "save history" );
  // 保存到 localStorage
  let arr = historyList.value;
  let cleaned = [];
  let new_arr = [];
  let mapp = Object();
  arr.forEach( ( x ) => {
    if ( !mapp[ x.value ] ) {
      cleaned.push( x.value );
      new_arr.push( x );
      mapp[ x.value ] = true;
    }
  } );
  arr = arr.slice( 0, max_history );
  localStorage.setItem( historystorekey, JSON.stringify( cleaned ) );
  //reset history
  historyList.value = new_arr;
};
let saveHistoryTask = null;
const SaveHistoryDelayed = ( q ) => {
  historyList.value.splice( 0, 0, { value: q } );
  if ( saveHistoryTask ) {
    clearTimeout( saveHistoryTask );
  }
  saveHistoryTask = setTimeout( () => {
    SaveHistory();
    saveHistoryTask = null;
  }, 10000 );
};
onUnmounted( () => {
  SaveHistory();
} );
onMounted( () => {
  try {
    let data = JSON.parse( localStorage.getItem( historystorekey ) );
    if ( data ) {
      data.forEach( ( x ) => {
        if ( typeof x === "string" ) historyList.value.push( { value: x } );
      } );
    }
    if ( !historyList.value ) historyList.value = [];
  } catch {
    historyList.value = [];
  }
} );
////
const BuildSpan = ( msg ) => {
  let lines = [];
  msg.split( "\n" ).forEach( ( x ) => {
    if ( x == "" ) lines.push( h( "br" ) );
    else lines.push( h( "p", { display: "inline" }, x ) );
  } );
  return lines;
};
const Alert = ( msg ) => {
  ElMessage( { message: h( "p", {}, [ h( "span", {}, "报错：" ), h( "span", {}, BuildSpan( msg ) ) ] ) } );
};
const Success = ( msg ) => {
  ElMessage.success( { message: h( "div", {}, BuildSpan( msg ) ) } );
}
const ToTraditional = () => {
  searchQuery.value = ConvertChinese( searchQuery.value );
};
const drawerToTraditional = () => {
  drawerQueryString.value = ConvertChinese( drawerQueryString.value );
};
const DontperformSearch = () => { };
const validateRegexp = ( query ) => {
  if ( query.length === 0 ) return true;
  try {
    const regex = new RegExp( query );
  } catch ( error ) {
    // 处理无效的正则表达式
    Alert( `正则表达式${ query }无效` );
    return false;
  }
  return true;
};
const construct_image_url = ( x ) => {
  return image_construct_url + x;
}
const performSearch = () => {
  if ( IsSearching.value ) {
    return;
  }
  let v = searchQuery.value.trim();
  //console.log( "搜索", v );
  SaveHistoryDelayed( v );
  submitSearchString( v );
}
const splitQuery = ( v ) => {
  let subqueries = v.split( " " ).filter( x => x !== "" );
  return subqueries;
}
const ValidateSubqueries = ( v ) => {
  return v.every( validateRegexp );
}
const saveSubmittedQuery = ( v, subqueries ) => {
  submittedQuery.value = v;
  submittedSubqueryCount.value = subqueries.length;
}
const clearResult = () => {
  searchResultCache.value = [];
  searchResults.value = [];
}
const constructSearchUrl = ( subqueries, params ) => {
  let url = server_url.replace( "%s", window.encodeURIComponent( subqueries.join( ' ' ) ) );
  if ( params ) {
    for ( let i in params ) {
      if ( params.hasOwnProperty( i ) ) {
        url += "&" + i + "=" + window.encodeURIComponent( params[ i ] );
      }
    }
  }
  return url;
}
const submitSearchString = ( v, params, cb ) => {
  //validate
  let subqueries = splitQuery( v );
  if ( !ValidateSubqueries( subqueries ) ) return false;
  //save last query
  saveSubmittedQuery( v, subqueries );
  //if it is empty, clear result
  if ( subqueries.length === 0 ) {
    clearResult();
    return;
  }
  IsSearching.value = true;
  let l = subqueries.length;
  let url = constructSearchUrl( subqueries, params );
  fetchSearch( url, cb || searchCallback );
}
const fetchSearch = ( url, cb ) => {
  fetch( url )
    .then( ( x ) => {
      return x.json();
    }, () => {
      Alert( "网络请求失败" );
    } )
    .then( ( x ) => {
      try {
        cb( x );
      } catch ( e ) {
        Alert( e.toString() );
        console.error( e );
      }
    } ).finally( () => {
      IsSearching.value = false;
    } );
};
const searchCallback = ( x ) => {
  let res = x.result;
  if ( !res ) {
    let errormsg = x.error;
    Alert( errormsg || "返回数据没给结果" );
    return false;
  }
  searchResults.value = [];
  if ( x.maxhit !== undefined ) {
    submittedMaxHit.value = Math.round( parseFloat( x.maxhit ) );
  }
  //console.log( res );
  let subqueries = splitQuery( submittedQuery.value );
  let s = convertSearchResultData( res, subqueries );
  searchResultCache.value = s;
  maxSubqueryCount.value = submittedMaxHit.value;
  if ( IsAlwaysSortByPriority.value ) {
    ApplyPrioritySorting( IsHideNoPriority.value );
  } else if ( IsHideNoPriority.value ) {
    searchResultCache.value = searchResultCache.value.filter( x => getpriority( x.id ) > 0 );
  }
  AddAFew();
}
const moreSearchCallback = ( x ) => {
  let res = x.result;
  if ( !res ) {
    let errormsg = x.error;
    Alert( errormsg || "返回数据没给结果" );
    return false;
  }
  if ( x.maxhit !== undefined ) {
    submittedMaxHit.value = Math.round( x.maxhit - 0 );
  }
  //console.log( "more result", res );
  let subqueries = splitQuery( submittedQuery.value );
  let s = convertSearchResultData( res, subqueries );
  searchResultCache.value.push( ...s );
  if ( IsAlwaysSortByPriority.value ) {
    ApplyPrioritySorting( IsHideNoPriority.value );
  } else if ( IsHideNoPriority.value ) {
    searchResultCache.value = searchResultCache.value.filter( x => getpriority( x.id ) > 0 );
  }
  AddAFew();
}
const convertSearchResultData = ( res, subqueries ) => {
  let s = [];
  res.forEach( ( r ) => {
    let content = r.data;
    let name = content.name || "?";
    let owner = content.owner || "未知";
    let text = content.sw || "";
    let char = r.char || [];
    for ( let i = 0; i < char.length; i++ ) {
      let d = char[ i ].urls;
      for ( let j = 0; j < d.length; j++ ) {
        d[ j ] = construct_image_url( d[ j ] );
      }
    }
    let { count, char_count, res, failed_q } = CountChars( text, subqueries );
    s.push( {
      name: name,
      owner: owner,
      sw: text,
      id: r.id || -1,
      chars: char,
      match_count: count,
    } );
  } );
  return s;
}
const LoadMore = () => {
  if ( IsSearching.value ) return;
  let hasmore = AddAFew();
  if ( !hasmore ) QueryMore();
}
const QueryMore = () => {
  let next_min = submittedMaxHit.value - 1;
  if ( next_min <= 0 ) return;
  let subqueries = splitQuery( submittedQuery.value );
  let url = constructSearchUrl( subqueries, { "min_match": next_min } );
  fetchSearch( url, moreSearchCallback );
}
const AddAFew = () => {
  let n = 10;
  let now = searchResults.value.length;
  let maxlen = searchResultCache.value.length;
  let target_len = now + n;
  if ( target_len > maxlen ) {
    target_len = maxlen;
    n = target_len - now;
  }
  if ( n <= 0 ) return false;
  for ( let i = now; i < target_len; i++ ) {
    searchResults.value.push( searchResultCache.value[ i ] )
  }
  return true;
};
// Highlight matched text
const highlightMatch = ( result, default_query ) => {
  if ( !result ) return "";
  let text = result.sw;
  if ( !text ) return;
  let query = result.currentquery;
  if ( !query ) {
    query = default_query;
  }
  if ( !query ) return text;
  //TODO fix this render bug
  text = PurgeText( text );
  let v = query.trim();
  if ( v.length === 0 ) return text;
  let subqueries = splitQuery( v );
  try {
    // Normal text search
    subqueries.forEach( function ( subquery ) {
      text = text.replace( RegExp( `(${ subquery })`, "g" ), `<mark>$1</mark>` );
    } );
    return text;
  } catch ( e ) {
    //console.log( "highlight error" );
    console.log( e );
    return text;
  }
};
const GetSelectionText = ( el ) => {
  if ( el ) {
    let start = el.selectionStart;
    let end = el.selectionEnd;
    if ( start !== end ) {
      return el.value.substring( start, end );
    }
  }
  const selection = window.getSelection();
  if ( selection.rangeCount > 0 ) {
    return selection.toString().trim();
  }
  else {
    return null;
  }
}
const OnSelectChangeOnText = ( result ) => {
  const selectedText = GetSelectionText();
  if ( selectedText ) {
    // 重新渲染带新选中文本的高亮内容
    result.currentquery = selectedText;
  }
  else {
    result.currentquery = undefined;
  }
}
const OnSearchTextSelectionChange = () => {
  const selectedText = GetSelectionText( textInputRef.value.inputRef.input );
  if ( selectedText && selectedText.length === 1 ) {
    let sim = get_similar_chars( selectedText );
    if ( sim ) {
      showPopover.value = true;
      similarChars.value = sim;
      popOverLeft.value = CalcPopoverLeft();
    }
  } else {
    showPopover.value = false;
  }
}
const CalcPopoverLeft = () => {
  console.log( "calc" )
  let el = textInputRef.value.inputRef.input;
  let fontsize = window.getComputedStyle( el ).fontSize;
  if ( !fontsize ) fontsize = 8;
  else fontsize = parseInt( fontsize );
  let numtokens = el.selectionStart;
  console.log( fontsize, numtokens );
  if ( !numtokens ) return 0;
  let left = fontsize * numtokens;
  console.log( "left", left );
  return left;
}
const get_similar_chars = ( char ) => {
  return GetVariable( char )
}
const CountChars = ( text, queries ) => {
  let count = 0;
  let char_count = 0;
  let chars = {};
  let result = [];
  let failed = [];
  for ( let i = 0; i < queries.length; i++ ) {
    let subq = queries[ i ];
    if ( subq.length > 0 ) {
      let flag = false;
      //collect all hit chars
      let hits = text.match( RegExp( `(${ subq })`, "g" ) );
      if ( hits ) {
        for ( let j = 0; j < hits.length; j++ ) {
          if ( !chars[ hits[ j ] ] ) {
            chars[ hits[ j ] ] = 1;
            result.push( hits[ j ] );
          }
          char_count++;
        }
        flag = true;
      }
      if ( flag ) {
        count++;
      } else {
        //failed
        failed.push( subq );
      }
    }
  }
  let res = result.join( "" );
  let failed_q = failed.join( " " );
  return { count, char_count, res, failed_q };
};
const GetCSVName = ( query ) => {
  let q = query.join( " " );
  q = q.replace( /[\r\n[]?!@&]/g, "_" );
  return `碑帖搜索结果_${ q }`;
};
const PurgeText = ( text ) => {
  text = text.replace( /[\r\n\ufeff 　]+/g, "" );
  return text;
}
const col_title = [ "index", "name", "owner", "match_count", "char_count", "hit_chars", "failed_queries" ];
const ExportSearchToCSV = () => {
  //将数据里的项目按照碑帖导出为CSV
  //表头：
  //    碑帖id
  //    碑帖名
  //    作者
  //    命中表达式个数
  //    命中字符统计（按表达式、出现排序）
  //    [匹配表达式...的命中次数]
  let data = [];
  let source = searchResultCache.value;
  let query = submittedQuery.value.split( " " );
  for ( let i = 0; i < source.length; i++ ) {
    let r = source[ i ];
    let id = r.id || -1;
    let owner = r.owner || "";
    let text = r.sw || "";
    text = PurgeText( text );
    let name = r.name || "";
    let { count, char_count, res, failed_q } = CountChars( text, query );
    data.push( [ id, name, owner, count, char_count, res, failed_q ] );
  }
  stringify( data, { columns: col_title, bom: true, header: true }, ( err, data_str ) => {
    Download( `${ GetCSVName( query ) }.csv`, data_str );
  } );
}
const Download = ( filename, text ) => {
  //console.log( "download", filename );
  let element = document.createElement( "a" );
  element.setAttribute( "href", `data:text/plain;charset=utf-8,${ encodeURIComponent( text ) }` );
  element.setAttribute( "download", filename );
  element.style.display = "none";
  document.body.appendChild( element );
  element.click();
  document.body.removeChild( element );
};
const OpenPanel = ( e, result ) => {
  selectedResult.value = result;
  drawerVisible.value = true;
  //selectedChars.value = [];
  drawerQueryString.value = submittedQuery.value;
  drawerTextContent.value.sw = selectedResult.value.sw;
  FetchFullImages(); // 加载全图
}
const FetchFullImages = () => {
  if ( selectedResult.value.images && selectedResult.value.images.length > 0 ) return; // 如果已经加载过全图，则不再重复加载（避免重复请求导致的问题
  let url = `${ server_host }/api/get_single_image_urls?id=${ selectedResult.value.id }`;
  fetch( url ).then( res => { return res.json() } ).then( data => {
    selectedResult.value.images = data.map( ( x ) => `${ server_host }/${ x }` );
  } );
};

// 自动补全的查询函数
const drawerQuerySearch = ( queryString, cb ) => {
  //console.log( '自动补全查询:', queryString );
  let subqueries = splitQuery( queryString ); // 拆分查询字符串为子查询数组
  if ( subqueries.length === 0 ) {
    cb( [] ); // 如果没有子查询，则直接返回空数组
    return;
  }
  let q = subqueries[ subqueries.length - 1 ]; // 取最后一个子查询作为当前搜索的字符
  if ( q.length !== 1 ) {
    // 如果输入的不是单个字符，则不进行搜索
    cb( [] );
    ElMessage.info( '请输入单个汉字' );
    return;
  }
  //console.log( '自动补全查询字符:', q );
  const results = FindChineseComponent( q );
  const r = [];
  results.forEach( item => {
    r.push( { value: item } );
  } );
  // 调用 callback 返回建议列表
  cb( r );
};
const selectedChars = ref( [] ); // 选中字符的数组
// 选中自动补全项时的处理函数
const drawerHandleSelect = ( item ) => {
  //console.log( '选中自动补全项:', item, drawerQueryString.value );
};
const drawerOldifyResult = ( t ) => {
  t.forEach( ( x ) => {
    x.old = true;
  } );
};
const drawerSearchChar = () => {
  let d = selectedResult.value;
  let t = selectedChars.value;
  drawerOldifyResult( t );
  let c = drawerQueryString.value;
  if ( c.length === 0 ) return;
  //fetch char info from server
  let qs = splitQuery( c );
  let allCandidates = new Set();
  qs.forEach( ( c ) => {
    let candidates = FindCharactersWithComponent( c, selectedResult.value.sw, allCandidates );
  } );
  allCandidates.forEach( ( c ) => {
    if ( selectedChars.value.every( ( y ) => y.char !== c ) ) {
      let url = `${ server_host }/api/getimage?id=${ d.id }&char=${ c }`;
      fetch( url ).then( ( res ) => { return res.json() } ).then( ( data ) => {
        t.splice( 0, 0, {
          "old": false,
          "char": c, "urls": data.map(
            ( x ) => { return `${ server_host }/${ x }` }
          )
        } );
      } );
    }
  } );
  //update query
  let newq = Array.from( allCandidates ).join( ' ' );
  drawerQueryString.value = newq;
}
const drawerCharRow = ( { row, rowIndex } ) => {
  return { "background-color": row.old ? 'var(--bg1)' : 'var(--bg0)' }
}
const clearDrawerChars = () => {
  selectedChars.value = [];
}
const onDrawerClose = ( done ) => {
  if ( true || !selectedChars.value.length ) { return done(); }
  ElMessageBox.confirm( '关闭面板将清除数据', '注意',
    {
      confirmButtonText: '知道了',
      cancelButtonText: '不要关闭',
      type: 'warning',
      customClass: 'drawer-close-confirm'
    } )
    .then( () => {
      done();
    } )
    .catch( () => {
      // catch error
    } )
}
const insertChar = ( char ) => {
  let inputEl = textInputRef.value.inputRef.input;
  if ( !inputEl ) return

  const startPos = inputEl.selectionStart
  const endPos = inputEl.selectionEnd

  // 替换当前选中内容
  searchQuery.value =
    searchQuery.value.substring( 0, startPos + 1 ) +
    char +
    searchQuery.value.substring( endPos )

  // 移动光标到插入字符之后
  setTimeout( () => {
    inputEl.focus();
    inputEl.setSelectionRange( startPos, startPos + 1 );
  }, 0 );

  //showPopover.value = false;
}
</script>
<script>
export default {
  name: "App",
  components: {},
};
</script>